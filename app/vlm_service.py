import io
import re
import base64
import torch
from PIL import Image, ImageDraw
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from peft import PeftModel

class SatQueryAI:
    def __init__(self, base_model_id: str = "Qwen/Qwen2-VL-2B-Instruct", lora_weights_path: str = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        print(f"[AI Engine] Loading processor and base model on {self.device}...")
        self.processor = AutoProcessor.from_pretrained(base_model_id)
        base_model = Qwen2VLForConditionalGeneration.from_pretrained(
            base_model_id,
            torch_dtype=self.dtype,
            device_map="auto"
        )

        if lora_weights_path:
            print(f"[AI Engine] Attaching LoRA weights from {lora_weights_path}...")
            self.model = PeftModel.from_pretrained(base_model, lora_weights_path)
        else:
            self.model = base_model

        self.model.eval()
        print("[AI Engine] Ready for user queries.")

    def run_inference(self, image_bytes: bytes, user_query: str, mode: str = "grounding"):
        """
        Accepts raw image bytes uploaded by the user and executes VQA or Grounding.
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = image.size

        if mode == "grounding":
            formatted_prompt = (
                f"Locate the {user_query} in the image. Reply ONLY with the bounding "
                "box coordinates in the exact format [ymin, xmin, ymax, xmax]."
            )
        else:  # General VQA / Classification
            formatted_prompt = user_query

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": formatted_prompt},
                ],
            }
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=128)

        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        raw_output = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # Coordinate parsing
        boxes = re.findall(r"\[([0-9.]+),\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+)\]", raw_output)
        detected_boxes = []
        draw = ImageDraw.Draw(image)

        for box in boxes:
            ymin, xmin, ymax, xmax = map(float, box)
            if max(ymin, xmin, ymax, xmax) <= 1.0:
                x1, y1, x2, y2 = int(xmin * w), int(ymin * h), int(xmax * w), int(ymax * h)
            else:
                x1, y1, x2, y2 = int(xmin * w / 1000), int(ymin * h / 1000), int(xmax * w / 1000), int(ymax * h / 1000)

            detected_boxes.append({"bbox": [x1, y1, x2, y2], "label": user_query})
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

        # Convert the processed image into a base64 string for immediate frontend rendering
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return {
            "query": user_query,
            "raw_text": raw_output,
            "boxes": detected_boxes,
            "image_dimensions": {"width": w, "height": h},
            "rendered_image": f"data:image/jpeg;base64,{image_base64}"
        }

# Singleton instance initialized once at startup
# To this (lazy loader):
_vlm_engine = None

def get_vlm_engine():
    global _vlm_engine
    if _vlm_engine is None:
        _vlm_engine = SatQueryAI()
    return _vlm_engine