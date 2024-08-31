import os
import sys
import json
import cv2
import numpy as np
import base64
from scipy.spatial.transform import Rotation as R
import open3d as o3d

# グローバル変数
reference_images = {}
reference_3d_models = {}
orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.2, nlevels=8)

# 検出のしきい値を15に設定
DETECTION_THRESHOLD = 15

def load_reference_data():
    # スクリプトのディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # メタデータの読み込み
    metadata_dir = os.path.join(script_dir, 'nfts', 'nft_metadata')
    for filename in os.listdir(metadata_dir):
        if filename.endswith('.json'):
            model_name = os.path.splitext(filename)[0]
            metadata_path = os.path.join(metadata_dir, filename)

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # 画像パスの修正
            image_path = os.path.join(script_dir, 'nfts', metadata['image_path'].lstrip('/'))
            
            # 画像の読み込みと特徴点の抽出
            if os.path.exists(image_path):
                image = cv2.imread(image_path, 0)
                image = cv2.resize(image, (640, 480))  # 画像サイズを統一
                kp, des = orb.detectAndCompute(image, None)
                if kp and des is not None:
                    reference_images[model_name] = {
                        'keypoints': kp,
                        'descriptors': des
                    }
                else:
                    print(f"Warning: No features detected in reference image {image_path}")
            else:
                print(f"Warning: Image file not found: {image_path}")

            # モデルパスの修正
            model_path = os.path.join(script_dir, 'nfts', metadata['model_path'].lstrip('/'))
            
            metadata['image_path'] = image_path
            metadata['model_path'] = model_path

            reference_3d_models[model_name] = metadata

    print(f"Loaded {len(reference_images)} reference images and {len(reference_3d_models)} 3D models")

def load_3d_model(model_path):
    mesh = o3d.io.read_triangle_mesh(model_path)
    return np.asarray(mesh.vertices)

def render_3d_model(vertices, image_size=(640, 480)):
    proj_matrix = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]])
    points_2d = proj_matrix @ vertices.T
    points_2d = points_2d[:2] / points_2d[2]
    points_2d = points_2d.T

    image = np.zeros(image_size, dtype=np.uint8)
    for point in points_2d:
        x, y = int(point[0]), int(point[1])
        if 0 <= x < image_size[1] and 0 <= y < image_size[0]:
            image[y, x] = 255

    return image

def estimate_pose(image_points, object_points):
    camera_matrix = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.zeros((4,1))

    _, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, dist_coeffs)

    rot_matrix, _ = cv2.Rodrigues(rvec)
    r = R.from_matrix(rot_matrix)
    quaternion = r.as_quat()

    return tvec.flatten(), quaternion

def detect_object(data):
    try:
        if 'image' not in data or not data['image']:
            raise ValueError("No image data received")

        # クライアントから送られてくるデータ形式に合わせて処理
        img_data = data['image']
        if isinstance(img_data, str) and img_data.startswith('data:image'):
            # Base64エンコードされた画像データの場合
            img_data = img_data.split(',')[1]
        
        img_data = base64.b64decode(img_data)

        if not img_data:
            raise ValueError("Empty image data after decoding")

        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None or img.size == 0:
            raise ValueError("Failed to decode image")

        # 入力画像のサイズを統一
        img = cv2.resize(img, (640, 480))

        # 画像の前処理
        img = cv2.equalizeHist(img)  # ヒストグラム平坦化
        img = cv2.GaussianBlur(img, (5, 5), 0)  # ガウシアンブラー

        kp_image, des_image = orb.detectAndCompute(img, None)

        if kp_image is None or des_image is None or len(kp_image) == 0:
            raise ValueError("No features detected in the image")

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        best_match = None
        max_good_matches = 0
        best_matches = None

        for model_name, ref_data in reference_images.items():
            matches = bf.match(ref_data['descriptors'], des_image)
            good_matches = [m for m in matches if m.distance < 40]  # 距離のしきい値を調整

            if len(good_matches) > max_good_matches:
                max_good_matches = len(good_matches)
                best_match = model_name
                best_matches = good_matches

        if best_match and max_good_matches >= DETECTION_THRESHOLD:
            metadata = reference_3d_models.get(best_match, {})
            return {
                'detected': True,
                'model_name': best_match,
                'num_matches': max_good_matches,
                'match_quality': f"{max_good_matches}/{DETECTION_THRESHOLD}",
                'confidence': f"{(max_good_matches / DETECTION_THRESHOLD) * 100:.2f}%",
                'metadata': metadata,
                'DETECTION_THRESHOLD': DETECTION_THRESHOLD
            }
        else:
            return {'detected': False, 'reason': 'Not enough good matches', 'num_matches': max_good_matches}
    except Exception as e:
        return {'error': str(e)}

def get_parent_info(parent_id):
    for model_name, metadata in reference_3d_models.items():
        if metadata.get('ID') == parent_id:
            return {
                'detected': True,
                'model_name': model_name,
                'metadata': metadata,
                'match_quality': 'N/A',
                'confidence': 'N/A',
                'num_matches': 'N/A',
                'DETECTION_THRESHOLD': DETECTION_THRESHOLD
            }
    return {'error': f'Parent ID {parent_id} not found'}

# メインの処理
if __name__ == '__main__':
    try:
        load_reference_data()
        for line in sys.stdin:
            try:
                data = json.loads(line)
                if 'get_parent_info' in data:
                    result = get_parent_info(data['get_parent_info'])
                else:
                    result = detect_object(data)
                print(json.dumps(result))
                sys.stdout.flush()
            except json.JSONDecodeError:
                print(json.dumps({'error': 'Invalid JSON input'}))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({'error': str(e)}))
                sys.stdout.flush()
    except Exception as e:
        print(json.dumps({'error': f"Initialization error: {str(e)}"}))
        sys.stdout.flush()