import os, yaml
import numpy as np
import untangle
import cv2 as cv
import time
from functools import lru_cache
from ultralytics import YOLO

SERVICE_NAME = 'IDA'

# Models
MODEL_DIR = '/pvc/models'

# Font
font = "NotoSans-Regular"
ft = cv.freetype.createFreeType2()
ft.loadFontData(fontFileName=f"/app/application/fonts/{font}.ttf", idx=0)

# Cache definition
cached_model = None
cached_version = None

def xml_to_opencv(features: str):
    black = (0, 0, 0)
    try:
        # Parsen der XML-Daten aus dem Header der URL
        doc = untangle.parse(features)

    except Exception as e:
        # print(e) 
        return
        
    for i, page in enumerate(doc.page):
        _, _, width, height = map(int, page["rect"].split(" "))

        sheet = np.zeros((height, width, 3), np.uint8)
        sheet.fill(255)

        try:
            for line in page.block.zeile:
                for word in line.word:
                    left, top, right, bottom = map(int, word["rect"].split(" "))

                    for engine in word.engine:
                        if engine["name"] == "pdftext":
                            word_text = engine["string"]
                        if engine["name"] == "nuance":
                            word_text = engine["string"]
                    try:
                        ft.putText(
                            img=sheet,
                            text=word_text,
                            org=(left, bottom),
                            fontHeight=32,
                            color=black,
                            thickness=-1,
                            line_type=cv.LINE_AA,
                            bottomLeftOrigin=True,
                        )
                    except Exception as e:
                        # print(e)
                        pass
        except Exception as e:
            pass

        try:
            for line in page.vlin:
                left, top, right, bottom = map(int, line["rect"].split(" "))
                cv.rectangle(sheet, (left, top), (right, bottom), black, -1)
        except Exception as e:
            pass
            

        try:
            for line in page.hlin:
                left, top, right, bottom = map(int, line["rect"].split(" "))
                cv.rectangle(sheet, (left, top), (right, bottom), black, -1)
        except Exception as e:
            pass
    
    return sheet 

@lru_cache(maxsize=2)
def load_model(qualifier: str, prefix: str, version: str):
    global cached_model, cached_version

    model = cached_model

    if model is None or version != cached_version:
        path = f"/pvc/models/IDA/_{qualifier}/{prefix}/{version}"
        model = YOLO(f"{path}/{version}.pt")
        cached_model = model
        cached_version = version
        
    return model

def predict(features: str, qualifier: str, prefix: str, model_version: str):

    QUALIFIER = '_' + qualifier

    results = []

    if prefix == '_ALL':
        # set start time
        start_time = time.time()
        print('+' * 100)

        # convert xml to opencv
        sheet_cv = xml_to_opencv(features = features)
        
        # set end time sheet
        end_time_sheet = time.time()

        # Load config
        config_file_path = os.path.join(MODEL_DIR, SERVICE_NAME, QUALIFIER, prefix, model_version, 'model_config.yaml')
        if os.path.exists(config_file_path):
            with open(config_file_path) as file:
                model_config = yaml.load(file, Loader=yaml.FullLoader)
        
        # Clear the cache
        if model_version != cached_version:
            load_model.cache_clear()

        # load model 
        yolo_model = load_model(qualifier = qualifier, 
                           prefix = prefix, 
                           version = model_version)
        
        end_time_load_model = time.time()
        
        # Predictions
        results = yolo_model.predict(sheet_cv, iou=0, verbose=True)

        end_time_predict_model = time.time()

        boxes = sorted(results[0].boxes.data, key=lambda x: x[1])

        results = []

        for box in boxes:
            left, top, right, bottom, conf, label_number = box.tolist()
            if label_number in model_config:
                label = model_config[label_number]
            rect = f"{int(left)} {int(top)} {int(right)} {int(bottom)}"
            
            result = {
                "Qualifier": label,
                "Rect": rect, 
                "Confidence": round(conf, 2)
            }
            results.append(result)


        # set end time
        end_time = time.time()
        
        # compute ProcessingTimeComplete(PTC) in ms; ProcessingTimeSheet(PTS(abs)) in ms; ProcessingTimeSheet(PTS(%))
        ptc = (end_time - start_time) * 1000
        ptsa = (end_time_sheet - start_time) * 1000
        ptsp = (100/ptc * ptsa)
        print("completeTime:" f"{ptc:.2f}""ms")
        print("xml_to_opencv:" f"{ptsa:.2f}""ms""    " f"{ptsp:.2f}""%")

        # ProcessingTimeLoadModel(PTLM(abs)) in ms; ProcessingTimeLoadModel(PTLM(%)) 
        ptlm = (end_time_load_model - end_time_sheet) * 1000
        ptlmp = (100/ptc * ptlm)
        print("load_model:" f"{ptlm:.2f}""ms""    " f"{ptlmp:.2f}""%")
        
        # ProcessingTimePredictModel(PTPM(abs)) in ms; ProcessingTimePredictModel(PTLM(%)) 
        ptpm = (end_time_predict_model - end_time_load_model) * 1000
        ptpmp = (100/ptc * ptpm)
        print("prediction:" f"{ptpm:.2f}""ms""    "f"{ptpmp:.2f}""%")
        
        # ProcessingTimePostprocessingModel(PTPR(abs)) in ms; ProcessingTimePostprocessingModel(PTPR(%)) 
        ptpr = (end_time - end_time_predict_model) * 1000
        ptprp = (100/ptc * ptpr)
        print("postprocess:" f"{ptpr:.2f}""ms""    "f"{ptprp:.2f}""%")
        print('+' * 100)
        
    return results