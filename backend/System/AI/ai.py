import joblib
import tflite_runtime.interpreter as tflite
from System.database.init import Database
import numpy as np


class AI:
    def __init__(self):
        self.interpreter = tflite.Interpreter(model_path="ANNmodel.tflite")
        self.interpreter.allocate_tensors()
        self.encoder = joblib.load("encoder.pkl")
        self.scaler = joblib.load("scaler.pkl")
        self.input_index = self.interpreter.get_input_details()[0]["index"]
        self.output_index = self.interpreter.get_output_details()[0]["index"]
        self.db = Database()

    def predict_ai(self):
        df = self.db.get_latest_ai_input()
        if df is None:
            print("❌ Không có dữ liệu AI input")
            return {"need_irrigation": None, "confidence": None}

        print("📌 Input gốc:")
        print(df)

        # Transform
        X = self.encoder.transform(df)
        print("📌 Sau encoder:", X)

        X = self.scaler.transform(X).astype(np.float32)
        print("📌 Sau scaler:", X)

        self.interpreter.set_tensor(self.input_index, X)
        self.interpreter.invoke()
        y = self.interpreter.get_tensor(self.output_index)[0][0]
        print("📌 Columns after encoder:", self.encoder.get_feature_names_out())
        print("📌 Output mô hình (raw y):", y)
        print("📌 Kết luận mô hình:", "Tưới" if y > 0.5 else "Không tưới")
        print("📌 Độ tin cậy:", float(y))

        return {"need_irrigation": int(y > 0.5), "confidence": float(y)}


ai = AI()
ai.predict_ai()
