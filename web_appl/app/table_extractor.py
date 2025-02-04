from transformers import AutoImageProcessor, TableTransformerForObjectDetection
import torch
from pdf2image import convert_from_path
import os

class TableExtractor:
    def __init__(self):
        self.image_processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")
        self.model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")

    def process_pdf(self, pdf_path):
        extracted_tables = []
        images = convert_from_path(pdf_path)
        
        for page_num, image in enumerate(images):
            inputs = self.image_processor(images=image, return_tensors="pt")
            outputs = self.model(**inputs)
            
            target_sizes = torch.tensor([image.size[::-1]])
            results = self.image_processor.post_process_object_detection(
                outputs, 
                threshold=0.8, 
                target_sizes=target_sizes
            )[0]
            
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                box = [round(i, 2) for i in box.tolist()]
                xmin, ymin, xmax, ymax = map(int, box)
                cropped_table = image.crop((xmin, ymin, xmax, ymax))
                
                # Save table image
                output_path = f"app/static/extracted_tables/extracted_table_page_{page_num + 1}.png"
                cropped_table.save(output_path)
                extracted_tables.append(output_path)
        
        return extracted_tables