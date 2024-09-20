import fitz  # PyMuPDF
from datetime import datetime

from Source.Handler import Handler

class ExtractPDFMeta(Handler):
    def handle(self, request):
        '''
        Текущий запрос:
            request = {
                'task': 'extract_meta',
                'path': './Data/PDF/text/text2.pdf'}
        '''
        if request['task'] == 'extract_meta':
            doc = fitz.open(request['path'])

            meta = doc.metadata

            meta_info = {
                'format': meta.get('format', 'Нет данных'),
                'author': meta.get('author', 'Нет данных'),
                'creator': meta.get('creator', 'Нет данных'),
                'title': meta.get('title', 'Нет данных'),
                'subject': meta.get('subject', 'Нет данных'),
                'keywords': meta.get('keywords', 'Нет данных'),
                'trapped': meta.get('trapped', 'Нет данных'),
                'encryption': meta.get('encryption', 'Нет данных'),
                'creation_date': self.convert_date(meta.get('creationDate', 'Нет данных')),
                'modification_date': self.convert_date(meta.get('modDate', 'Нет данных')),
                'producer': meta.get('producer', 'Нет данных')
            }

            request['meta'] = meta_info

            print(f"[ Debug ] ExtractPDFMeta: Обработано")
            print(request['meta'])
            request['task'] = 'extract_text'
            return super().handle(request)
        else:
            print("[ Debug ] Error during handing (Mets)")
            return super().handle(request)
        

    def convert_date(self, date):
        if date.startswith('D:'):
            date = date[2:]

        try:
            parsed_date = datetime.strptime(date[:14], '%Y%m%d%H%M%S')
            readable_date = parsed_date.strftime('%d.%m.%Y %H:%M:%S')
            return readable_date
        except ValueError:
            return "Unknown"
        


if __name__ == "__main__":
    reader = ExtractPDFMeta()

    # Ручной запрос
    manual_request = {'task': 'extract_meta',
                      'path': "./Data/PDF/text/text2.pdf"}
    
    reader.handle(manual_request)

    print(f"Мета-данные документа: {manual_request.get('meta')}")
