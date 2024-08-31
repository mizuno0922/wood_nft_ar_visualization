import cv2
import numpy as np

def extract_wood(image_path, output_path):
    # 画像を読み込む
    image = cv2.imread(image_path)
    
    # 赤色のマーカーを検出
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    
    # マーカーの輪郭を見つける
    contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) >= 2:
        # 面積順に上位2つの輪郭を選択
        largest_contours = sorted(contours, key=cv2.contourArea, reverse=True)[:2]
        
        # 2つのマーカーの座標を取得
        coords = [cv2.boundingRect(c) for c in largest_contours]
        
        # バウンディングボックスの座標を計算
        x1 = min(coords[0][0], coords[1][0])
        y1 = min(coords[0][1], coords[1][1])
        x2 = max(coords[0][0] + coords[0][2], coords[1][0] + coords[1][2])
        y2 = max(coords[0][1] + coords[0][3], coords[1][1] + coords[1][3])
        
        # バウンディングボックスの内側を切り取る
        roi = image[y1:y2, x1:x2]
        
        # グリーンバックを削除
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        mask_green = cv2.inRange(hsv_roi, lower_green, upper_green)
        mask_green = cv2.bitwise_not(mask_green)
        
        # 木材部分のみを抽出
        wood = cv2.bitwise_and(roi, roi, mask=mask_green)
        
        # アルファチャンネルを追加（透明な背景）
        b, g, r = cv2.split(wood)
        alpha = mask_green
        wood_rgba = cv2.merge((b, g, r, alpha))
        
        # 結果を保存（PNG形式）
        cv2.imwrite(output_path, wood_rgba)
        print(f"処理が完了しました。結果は {output_path} に保存されました。")
    else:
        print("2つの赤いマーカーが見つかりませんでした。")

# 使用例
input_image = '/home/sakiya03/デスクトップ/self_dev/WoodNFT/webar-project/nfts/images/49.JPG'
output_image = 'output.png'
extract_wood(input_image, output_image)
