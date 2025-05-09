import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import psycopg2
import pymupdf 
import subprocess

import torch
import time

import os

from dedoc import DedocManager
from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import DocxConverter, PNGConverter, ConverterComposition
from dedoc.metadata_extractors import BaseMetadataExtractor, MetadataExtractorComposition
from dedoc.readers import DocxReader, PdfAutoReader, PdfImageReader, ReaderComposition
from dedoc.structure_extractors import DefaultStructureExtractor, StructureExtractorComposition
from dedoc.structure_constructors import TreeConstructor, StructureConstructorComposition

dedoc_manager = DedocManager(
    manager_config={
        "attachments_handler": AttachmentsHandler(),
        "converter": ConverterComposition([DocxConverter(), PNGConverter()]),
        "reader": ReaderComposition([DocxReader(), PdfAutoReader(), PdfImageReader()]),
        "structure_extractor": StructureExtractorComposition(extractors={DefaultStructureExtractor.document_type: DefaultStructureExtractor()}, default_key=DefaultStructureExtractor.document_type),
        "structure_constructor": StructureConstructorComposition(constructors={"tree": TreeConstructor()}, default_constructor=TreeConstructor()),
        "document_metadata_extractor": MetadataExtractorComposition([BaseMetadataExtractor()])
    }
)


class DocumentLoader:
    def __init__(self):
        # self.source_directory = source_directory
        # self.db_table = db_table
        self.source_directory = None
        self.db_table = None
        self.connection = None


    def get_db_connection(self):
        self.connection = psycopg2.connect(database='happy_db', 
                                           user="happy_user", 
                                           password="happy", 
                                           host="postgre", 
                                           port="5432")
        return 0
    
    def close_db_connection(self):
        self.connection.close()

    def set_directory(self, directory):
        self.source_directory = directory

    def set_dbtable(self, table):
        self.db_table = table

    def log_message(self, message, level):
        logger_path = 'DocumentAnalysisSystem/Utility/Loader/logs.txt'
        level = '\t'*int(level)
        with open(logger_path, 'a') as f:
            f.write(f'{level}{message}\n')

    def elibrary_load(self):
        self.get_db_connection()
        with self.connection.cursor() as cursor:
            cursor.execute(f'''
                SELECT filename
                FROM {self.db_table}
            ''')
            already_uploaded = [item[0] for item in cursor.fetchall()]
        
        with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
            f.write(f'GPU is available\n') if torch.cuda.is_available() else f.write('Computing on CPU\n')
            f.write(f'\tScanning from `{self.source_directory}` directory\n')


        for document in os.listdir(self.source_directory):
            document_path = self.source_directory + '/' + document
            tag = document_path.split('/')[-2]

            # Проверка - загружен ли уже документ?
            if document in already_uploaded:
                print(f'[ DEBUG ] Documnet {document} is already uploaded')
                with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
                    f.write(f'\t\tDocumnet `{document}` is already uploaded\n')
                continue
            else:
                if document[document.rfind('.')+1:].lower() in ['pdf', 'doc', 'docx']:
                    text_dedoc = None
                    tables = None

                    # Сканирование с помощью DeDoc
                    try:
                        start = time.time()
                        text_dedoc, tables = self.dedoc_scan(document_path)
                        stop = time.time() - start
                        with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
                            f.write(f'\t\tDocument {document} was scanned in {stop} sec\n')
                    except Exception as err:
                        print(f'[ ERROR ] Error during OCR \n>>> {err}')
                        with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
                            f.write(f'\t\t[ ERROR ] Error during OCR\n\t\t\t{err}\n')
                        continue

                    # Загрузка в базу данных
                    if text_dedoc:
                        self.db_load(document, text_dedoc, tables, tag)

                else:
                    print(f'[ DEBUG ] Documnet {document} format is not supported')
                    continue

        print(f'[ DEBUG ] All documents has been uploaded!')
        with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
            f.write(f'All documents has been uploaded!\n')
        self.close_db_connection()

    
    def db_load(self, document, text_dedoc, tables, tag):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f'''
                    INSERT INTO {self.db_table} (filename, text_dedoc, tag)
                    VALUES (%s, %s, %s);''',
                    (document,text_dedoc,tag,))

                if tables:
                    for table in tables:
                        cursor.execute(f'''
                            INSERT INTO {self.db_table}_tables (doc_id, rows)
                            VALUES (
                                (SELECT id 
                                FROM elibrary_dataset 
                                ORDER BY ID DESC LIMIT 1), %s)
                        ''', (table,))

            self.connection.commit()
            print(f'[ DEBUG ] Documnet {document} has successfuly uploaded')
            return 0
        except Exception as err:
            with open('DocumentAnalysisSystem/Utility/Loader/logs.txt', 'a') as f:
                f.write(f'\t\t[ ERROR ] Document {document} cant be loaded:\n\t\t\t{err}\n')


    def dedoc_scan(self, path):
        text_dedoc = ''
        parsed_document = dedoc_manager.parse(path)
        sentences_list = self.concat_subpara([], parsed_document.content.structure)
        tables = self.read_tables(parsed_document.content.tables)
        print(parsed_document.content.tables)
        text_dedoc = '\n'.join(sentences_list)
        return text_dedoc, tables
    
    def concat_subpara(self, sentence, paragraph):
        sentence.append(paragraph.text)
        if len(paragraph.subparagraphs) > 0:
            for par in paragraph.subparagraphs:
                self.concat_subpara(sentence, par)
        return sentence

    def read_tables(self, tables):
        tables_list = []
        for table in tables:
            rows = [[cell.get_text() for cell in row] for row in table.cells]
            tables_list.append(rows)
        return tables_list
