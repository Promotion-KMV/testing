from loguru import logger
import core
lst_link = [
	
	# 'https://www.examtopics.com/exams/oracle/1z0-997-20/',
	# 'https://www.examtopics.com/exams/oracle/1z0-931/',
	# 'https://www.examtopics.com/exams/oracle/1z0-931-20/'

]
error_link = []
for i in lst_link:
    try:
    	settings = core.settings("config.json")
    	browser = core.browser(settings)
    	worker = core.worker(browser, settings)
    	worker.parse_full_exam(i, settings)
    	logger.info(f'exam {i} close')
    	browser.close()
    except:
        error_link.append(i)
        logger.error(i)

logger.info(error_link)
