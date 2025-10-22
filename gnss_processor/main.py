import os

import matplotlib
matplotlib.use('Agg')

from config import RAW_DATA_PATH, logger

from gnss_processor.app.pipline.data_processing_pipeline import DataProcessingPipeline


if __name__ == "__main__":
    """
    Основная функция для запуска пайплайна обработки.
    """
    
    pipeline = DataProcessingPipeline()
    
    # Обработка всех RINEX файлов в директории
    for rinex_file in os.listdir(RAW_DATA_PATH):
        if rinex_file.endswith('.h5') and os.path.isfile(os.path.join(RAW_DATA_PATH, rinex_file)):
            date_str = rinex_file.split('.')[0]
            
            success = pipeline.process_date(date_str)
            
            if success:
                logger.info(f"Successfully processed {rinex_file}")
            else:
                logger.error(f"Failed to process {rinex_file}")
