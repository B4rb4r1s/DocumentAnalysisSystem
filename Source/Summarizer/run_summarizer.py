from DB_Handler import DatabaseHandler
from OmegaSummarizer import Omega_summarizer

import config


def run_and_load():
    db_handler = DatabaseHandler(host='docker')
    db_handler.set_doc_ids()

    summarizers = [Omega_summarizer(model_path, device=config.DEVICE) for model_path in config.SUMMARY_MODELS]

    for summarizer in summarizers:
        summarizer.run_and_load(db_handler, 'elibrary_dataset_summaries.doc_id <= 5140 and elibrary_dataset_summaries.doc_id > 5120')

    db_handler.close_db_connection()


def run_test():
    summarizers = [Omega_summarizer(model_path) for model_path in config.SUMMARY_MODELS]
    
    for summarizer in summarizers:
        print(summarizer.summarize_text('''
В последнее время в современной России активизировались дискуссии на тему
«проблем молодежи», «молодежных ценностей», «будущего молодежи» и т.д. Интерес к
молодежи как социальной группе не случаен и проявляется со стороны не только научных
исследователей, но и органов власти, политических движений. Хотя очевидна
парадоксальность общего подхода к проблемам молодежи: в настоящее время молодежь
как единая социальная группа отсутствует, что еще было возможным в советское время. В
наши же дни молодежь как единое целое объединяют, возможно, только возрастные
рамки. Все остальные явления только усиливают современные диспропорции: различные
социально-экономические, имущественные возможности, несопоставимые стартовые
условия, политические интересы, серьезные региональные различия – всё это, скорее,
приводит к классовому расслоению, затрудняя использование обобщенных подходов к
изучению молодежи как социальной группы.
        '''))


if __name__ == '__main__':
    run_and_load()