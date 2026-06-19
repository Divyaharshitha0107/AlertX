from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

def detect_video(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return "Error: Could not open video", 0
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Sample every Nth frame to speed up processing (process 1 frame per second)
        frame_interval = max(1, int(fps)) if fps > 0 else 30
        
        detections = 0
        frames_processed = 0
        confidence_sum = 0
        confidence_count = 0
        frame_count = 0
        
        while True:
            success, frame = cap.read()
            
            if not success:
                break
            
            frame_count += 1
            
            # Only process every Nth frame
            if frame_count % frame_interval != 0:
                continue
            
            frames_processed += 1
            
            # Limit to first 300 frames to avoid long processing
            if frames_processed > 300:
                break
            
            try:
                results = model(frame, verbose=False)
                
                for r in results:
                    detections += len(r.boxes)
                    
                    for box in r.boxes:
                        confidence_sum += float(box.conf)
                        confidence_count += 1
            except Exception as e:
                print(f"Error processing frame {frame_count}: {str(e)}")
                continue
        
        cap.release()
        
        if frames_processed == 0:
            return "Error: No frames could be processed", 0
        
        average = detections / max(frames_processed, 1)
        
        if average < 2:
            alert = "Low Suspicious"
        elif average < 5:
            alert = "Medium Suspicious"
        else:
            alert = "High Suspicious"
        
        if confidence_count > 0:
            avg_confidence = round(
                (confidence_sum / confidence_count) * 100,
                2
            )
        else:
            avg_confidence = 0
        
        print(f"Detection complete: {alert}, Confidence: {avg_confidence}%")
        return alert, avg_confidence
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        return error_msg, 0