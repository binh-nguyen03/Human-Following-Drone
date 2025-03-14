# HOG + SVM -> Optical Flow -> KCF tracker
import cv2
import numpy as np
import time
import os
os.system('cls') 
# Hog + SVM
def gamma_correction(image, gamma):
    # Chuyển đổi ảnh về khoảng [0,1]
    norm_image = image / 255.0
    # Áp dụng công thức gamma correction
    corrected_image = np.power(norm_image, gamma) #np.power là hàm luỹ thừa
    # Chuyển về 0-255
    return (corrected_image * 255).astype(np.uint8)

person_detected = False  # Trạng thái ban đầu: chưa thấy người
last_detection_time = 0  # Lưu thời gian lần cuối cùng phát hiện người

DELAY_TIME = 1  # Thời gian chờ trước khi thông báo tiếp (giây)

# Khởi tạo HOG + SVM
# Cấu hình các tham số
cell_size = (8, 8)  # Kích thước ô (có thể đổi thành (16,16) để giảm độ phức tạp)
block_size = (16, 16)  # Kích thước khối (thường gấp đôi cell_size) hoặc (32, 32)
block_stride = (8, 8)  # Bước nhảy giữa các khối 
nbins = 9   # Số hướng của gradient có thể là 12

# Tạo bộ trích xuất HOG
hog = cv2.HOGDescriptor(
    _winSize=(64, 128),  # Kích thước cửa sổ phát hiện người
    _blockSize=block_size,
    _blockStride=block_stride,
    _cellSize=cell_size,
    _nbins=nbins
)
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

cap = cv2.VideoCapture(0)  # Mở camera cle
if not cap.isOpened():
    print("Không thể mở camera. Kiểm tra lại kết nối!")
else:
    print("Đã mở cam")
    
# Đặt độ phân giải camera (giúp tăng tốc)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15)
print ('cai xong do phan giai')

while True:
    ret, frame = cap.read()
    if not ret:
        break  # Thoát nếu không có dữ liệu từ camera
    
    # frame= cv2.GaussianBlur(frame, (5,5), sigmaX=1.0, sigmaY=1.0)  # Làm mịn Gaussian
    frame1 = gamma_correction(frame, gamma=1.5)  # Điều chỉnh gamma
    gray= cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)  # Chuyển sang ảnh xám
    # Tiền xử lý
    # Resize ảnh để giảm tải xử lý
    gray = cv2.resize(gray, (320, 240))
    # # Chuyển đổi sang kiểu float (giá trị từ 0 đến 1)
    # img = np.float32(gray) / 255.0
    # # Tính toán gradient theo hướng x và y
    # gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
    # gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3) 
    # # ksize là bộ lọc có kích thước mình chọn như 1 3 5 7 
    # # vd ksize = 1 là bộ lọc [-1 0 1]
    # # Tính độ lớn của gradient
    # gray= cv2.magnitude(gx, gy)

    # # Chuẩn hóa về khoảng 0-255 để sử dụng HOG
    # gray= cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Dùng canny để detect biên 
    I_canny = cv2.Canny(gray, 120, 250)
    # Phát hiện người bằng HOG + SVM
    boxes, weights = hog.detectMultiScale(I_canny, winStride=(4, 4), padding=(8, 8), scale=1.02)
    #boxes: Danh sách các tọa độ của hộp giới hạn (bounding boxes) chứa người được phát hiện.
    # Đây là một danh sách gồm nhiều tuple (x, y, w, h), trong đó:
    # x, y: Tọa độ góc trên bên trái của hộp.
    # w, h: Chiều rộng và chiều cao của hộp.
    # weights: Danh sách các trọng số tin cậy (confidence scores) tương ứng với mỗi hộp.
    # Scale: xác định tỷ lệ thay đổi kích thước ảnh trong quá trình dò tìm. 
    #        Nó giúp phát hiện người ở nhiều kích thước khác nhau trong ảnh/video.
    #        Khi detectMultiScale chạy, nó sẽ giảm kích thước ảnh dần dần và áp dụng HOG-SVM lên từng phiên bản nhỏ hơn.
    #        Nếu có người ở xa camera (nhỏ hơn trong khung hình), model vẫn có thể nhận diện được nhờ thay đổi tỷ lệ.
    #        Nếu scale quá nhỏ → Tốn tài nguyên, chậm. Nếu quá lớn → Có thể bỏ sót người.

    print('boxes',boxes)
    print('weight',weights)
    
    conf_threshold = 1.5 # Ngưỡng tin cậy (tùy chỉnh)
    filtered_persons = []
    for i in range(len(boxes)):
        if weights[i] > conf_threshold:
         filtered_persons.append(boxes[i])
     
    current_time = time.time()  # Lấy thời gian hiện tại
    if len(filtered_persons) > 0:
        if not person_detected:  # Nếu trước đó chưa thấy người, giờ mới thấy
            if current_time - last_detection_time > DELAY_TIME:
                print("NhậN thấy người!")  
                person_detected = True
                last_detection_time = current_time  # Cập nhật thời gian phát hiện
    else:
        if person_detected:  # Nếu trước đó thấy mặt, giờ không thấy nữa
            if current_time - last_detection_time > DELAY_TIME:
                print("Không phát hiện thấy người.")
                person_detected = False
                last_detection_time = current_time  # Cập nhật thời gian mất nhận diện
    # Vẽ khung xung quanh người phát hiện được
    for (x, y, w, h) in filtered_persons:
        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)  
        
    cv2.imshow("Canny", I_canny)
    cv2.imshow("Detected Persons", frame1)  # Hiển thị kết quả
    cv2.imshow("In put ch xu ly", frame) # hiển thị khi chưa qua xử lý
    
    if cv2.waitKey(1) & 0xFF == 27:  # Nhấn ESC để thoát
        break

cap.release() # giải phóng bộ nhớ khi tắt cam
cv2.destroyAllWindows()