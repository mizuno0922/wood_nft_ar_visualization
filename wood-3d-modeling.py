import cv2
import numpy as np
import pyvista as pv

def detect_wood_contour(image_path):
    # 画像を読み込む
    image = cv2.imread(image_path)
    
    # BGR色空間からHSV色空間に変換
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 緑色の範囲を定義（この値は調整が必要かもしれません）
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    
    # 緑色の範囲内のピクセルをマスク
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # マスクを反転（緑色以外の領域を取得）
    mask = cv2.bitwise_not(mask)
    
    # ノイズ除去
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 輪郭を検出
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 最大の輪郭を木材の輪郭とする
    wood_contour = max(contours, key=cv2.contourArea)
    
    return wood_contour

def create_3d_model(contour, thickness):
    # 輪郭から2Dポリゴンを作成
    points = contour.squeeze()
    
    # 2D点を3D点に変換
    points_3d = np.column_stack((points, np.zeros(len(points))))
    
    # PyVista Polyに変換
    poly = pv.PolyData(points_3d)
    poly['elevation'] = np.zeros(len(points_3d))
    
    # 押し出しで3Dモデルを作成
    extruded = poly.extrude((0, 0, thickness))
    
    return extruded

def main(image_path, thickness):
    # 木材の輪郭を検出
    contour = detect_wood_contour(image_path)
    
    # 3Dモデルを作成
    model = create_3d_model(contour, thickness)
    
    # モデルを表示または保存
    model.plot(show_edges=True)
    model.save('wood_model.stl')

# メイン処理
image_path = '/home/sakiya03/デスクトップ/self_dev/WoodNFT/webar-project/IMG_2272.JPG'  # ここに実際の画像パスを指定してください
thickness = 20  # mm
main(image_path, thickness)

# デバッグ用：検出された輪郭を表示
def debug_show_contour(image_path, contour):
    image = cv2.imread(image_path)
    cv2.drawContours(image, [contour], 0, (0, 255, 0), 2)
    cv2.imshow('Detected Contour', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# デバッグ用の関数呼び出し
contour = detect_wood_contour(image_path)
debug_show_contour(image_path, contour)