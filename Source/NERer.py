# This Python file uses the following encoding: utf-8
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import torch

import spacy
import datetime

from Source.Handler import Handler

import sys
sys.stdout.flush()


# Установка параметров работы модели
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f'[{datetime.datetime.now()}][ DEBUG ] Computing using device - {device}')


# tokenizer = AutoTokenizer.from_pretrained(PATH)
# model = AutoModel.from_pretrained(PATH)

# MODEL_NAME = 'kontur-ai/sbert_punc_case_ru'
# MODEL_PATH = 'Models_all/sbert-NER'

# ***** BEST *****
MODEL_NAME = 'FacebookAI/xlm-roberta-large-finetuned-conll03-english'
MODEL_PATH = 'Models_all/fb-roberta-NER'



# tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
# model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)


class NamedEntityRecognitionHandler(Handler):
    def __init__(self):
        super().__init__()
        # Выбор устройства обработки
        # spacy.prefer_gpu()
        # Загружаем предобученную модель spaCy
        self.nlp = spacy.load("ru_core_news_lg")

    def handle(self, request):
        # Проверяем, нужно ли выполнять выделение сущностей
        if 'text' in request and request['task'] == 'extract_entities':

            # HuggingFace Models
            # classifier = pipeline("ner", model=model, tokenizer=tokenizer)
            # entities = classifier(request['text'])

            # SpaCy Models
            doc = self.nlp(request['text'])
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            
            # Сохраняем выделенные сущности в запросе
            request['entities'] = entities
            
            print(f"[{datetime.datetime.now()}][ Debug ] NamedEntityRecognitionHandler: Обработано")
            print(request['entities'])
            return super().handle(request)
        else:
            print(f"[{datetime.datetime.now()}][ Debug Error ] Error during handing (NER)")
            return super().handle(request)



if __name__ == '__main__':
    # Пример использования NamedEntityRecognitionHandler для тестирования
    ner_handler = NamedEntityRecognitionHandler()
    
    # Создаем тестовый запрос с текстом
    request = {
        'task': "extract_entities",
        'text': "Высота башни составляет 324 метра (1063 фута), примерно такая же высота, как у 81-этажного здания, и самое высокое сооружение в Париже. Его основание квадратно, размером 125 метров (410 футов) с любой стороны. Во время строительства Эйфелева башня превзошла монумент Вашингтона, став самым высоким искусственным сооружением в мире, и этот титул она удерживала в течение 41 года до завершения строительство здания Крайслер в Нью-Йорке в 1930 году. Это первое сооружение которое достигло высоты 300 метров. Из-за добавления вещательной антенны на вершине башни в 1957 году она сейчас выше здания Крайслер на 5,2 метра (17 футов). За исключением передатчиков, Эйфелева башня является второй самой высокой отдельно стоящей структурой во Франции после виадука Мийо.",
        'steps': []
    }
    
    # Запускаем обработку
    ner_handler.handle(request)
    
    # Печатаем результат выделения сущностей
    print(f"Именованные сущности: {request.get('entities')}")





# DEEPPAVLOV
# ner_collection3_bert
# from deeppavlov import configs, build_model

# import PDFReader as reader

# def recognize(text):
#     # ner_model = build_model('ner_collection3_bert')
#     ner_model = build_model('ner_rus_bert', download=True, install=True)
#     # ner_model = build_model('ner_rus')

#     text_split = text.split('.')

#     return ner_model(text_split)


# if __name__ == '__main__':
#     path = './Data/PDF/text/text2.pdf'

#     text = reader.extract_text_from_pdf(path)
#     print(recognize(text))
