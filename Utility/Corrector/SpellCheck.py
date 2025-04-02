import os
import re
import tqdm
import time

import psycopg2
import json
import torch

import config
import SpellModels



class BaseSpellCorrector:
    def __init__(self, model_path, column=None, device=None):
        self.model_path = model_path
        self.device = device or "cuda:0" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer =  None
        self.column = column

        self.batch_size = 190

        self.tokenization_args = {}
        self.generation_args = {}

        self.encodings = {'input_ids': torch.tensor([[]])}
        print(f'Computing using GPU') if self.device=='cuda:0' else print(f'Computing using CPU')
        self.set_model()
    
    def set_model(self):
        raise NotImplementedError("Метод set_model должен быть реализован в подклассе.")
    
    def set_generation_arguments(self):
        raise NotImplementedError("Метод set_generation_arguments должен быть реализован в подклассе.")
    
    def decode(self, generated_tokens, **kwargs):
        return self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True, **kwargs)[0]

    
    def correct_text(self, text):
        corrected_paragraphs = []
        if self.column == 'fred_t5_large_spell':
            text = 'Исправь: """' + text +'"""'

        # for i, paragraph in enumerate(tqdm.tqdm(text.split('\n'), desc="Processing text paragraphs")):
        for i, paragraph in enumerate(text.split('\n')):

            tokens = self.tokenizer.encode(paragraph)
            if len(tokens) > self.batch_size:
                corrected_chunk = []
                start = time.time()

                token_chunks = [tokens[i:i+self.batch_size] for i in range(0, len(tokens), self.batch_size)]
                text_chunks = [self.tokenizer.decode(chunk, skip_special_tokens=True) for chunk in token_chunks]

                for text_chunk in text_chunks:

                    self.encodings = self.tokenizer(text_chunk, **self.tokenization_args, return_tensors="pt").to(self.device)
                    self.set_generation_arguments()

                    generated_tokens = self.model.generate(**self.encodings, **self.generation_args).to(self.device)

                    corrected_chunk.append(self.decode(generated_tokens))

                corrected_paragraph = ' '.join(corrected_chunk)
                stop = time.time() - start

            else:

                self.encodings = self.tokenizer(paragraph, **self.tokenization_args, return_tensors="pt").to(self.device)
                self.set_generation_arguments()

                start = time.time()
                generated_tokens = self.model.generate(**self.encodings, **self.generation_args).to(self.device)
                stop = time.time() - start

                with open('Happy/Utility/Corrector/logs.txt', 'a') as res:
                    res.write(f'\t\t\tParagraph {i}: {len(paragraph)} charecters proccesed in {stop} sec\n')

                corrected_paragraph = self.decode(generated_tokens)

            corrected_paragraphs.append(corrected_paragraph)
        
        corrected_text = '\n'.join(corrected_paragraphs)
        return corrected_text

    
    def run_and_load(self, db_handler=None, extra_condition=None):
        dataset = db_handler.get_db_table(table=config.SPELL_CORRECTION_TABLE, 
                                          column=self.column, 
                                          extra_condition=extra_condition)
        for doc_id, text in tqdm.tqdm(dataset, desc=f"Processing {self.column}"):
            try:
                with open('Happy/Utility/Corrector/logs.txt', 'a') as f:
                    f.write(f'\t\tDocument: {doc_id}\n')

                start = time.time()
                config.logger.debug(f"Обработка документа {doc_id}")
                processed_text = config.WHITESPACE_HANDLER(text)
                correction = self.correct_text(processed_text)
                stop = time.time() - start

                db_handler.upload_data(
                    table=config.SPELL_CORRECTION_TABLE, 
                    column=self.column, 
                    doc_id=doc_id, 
                    text=correction
                )
                with open('Happy/Utility/Corrector/logs.txt', 'a') as f:
                    f.write(f'\t\tDocument loaded in {stop} seconds\n')
            except Exception as err:
                config.logger.error(f"[ ERROR ] Документ {doc_id}: {err}")
        return






def make_dataset_from_json(json_file):
    dataset = []
    target = []
    # for json in jsons:
    file = open(json_file, "r", encoding="utf-8")
    for i, line in enumerate(file):
        line = line.strip()
        if not line:
            continue  # пропускаем пустые строки
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            print("Ошибка при разборе строки:", e)
            continue
        dataset.append([i, record.get("source")])
        target.append([i, record.get("correction")])
    return dataset, target



def run():
    corr = SpellModels.Omage_corrector('./Happy/Models/SpellCheck/ai-forever--FRED-T5-large-spell')
    # corr = SpellModels.Omage_corrector('./Happy/Models/SpellCheck/UrukHan--t5-russian-spell')

    text = 'Проблнма изучания социокультурных особенностей формирования социального потенциаламолодежи в усл овиях происхлдящих кризисных явленийи трансформаци российского общества является многоаспектной.'
    print(f'original: {text}\ncorrect: {corr.correct_text(text)}')
    


if __name__ == '__main__':
    run()
    # run_full_correction()