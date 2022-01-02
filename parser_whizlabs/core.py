import json
import random
import re
import time

from loguru import logger


import requests
from time import sleep

from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from openpyxl import Workbook
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# from twocaptcha import TwoCaptcha

class settings:
    def __init__(self, filename):
        file = open(filename, "r")
        self.fields = json.load(file)

    def get_field(self, fieldname):
        if fieldname in self.fields:
            return self.fields[fieldname]
        else:
            return False

class browser:
    #Настройки браузера подробнее https://peter.sh/experiments/chromium-command-line-switches/
    def __init__(self, settings):
        options = webdriver.ChromeOptions()
        if settings.get_field("hidden") == True:
            options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-logging-redirect")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-in-process-stack-traces")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_argument("--output=/dev/null")
        self.window = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.window.set_window_size(1200, 1100)
    def close(self):
        self.window.close()

class worker:
    def __init__(self, browser, settings):
        self.window = browser.window
        self.settings = settings

    def parse_full_exam(self, link, settings):
        datamassive = {"questions" : {}}
        self.login(settings)
        self.window.get(link)
        datamassive["exam_info"] = self.get_exam_info()
        json_file_name = self.get_exam_info()['exam_long_name']
        find_exam = self.window.find_elements(By.XPATH, '//*[@id="simple-tabpanel-0"]/div/div/div/div')
        logger.info(find_exam)
        count = len(self.get_button())

        datamassive["questions"].update(self.parse_questions(count))
        with open(f"{json_file_name}.json", "w") as stream:
            json.dump(datamassive, stream)

    def login(self, settings):
        self.window.get("https://www.whizlabs.com/")
        sleep(1)
        WebDriverWait(self.window, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "link-signin"))
        ).click()
        sleep(1)
        self.window.find_element_by_xpath('//*[@id="wrapper"]/div[3]/div/div/div[2]/form/div/div[1]/input').send_keys(settings.get_field("login"))
        self.window.find_element_by_xpath('//*[@id="wrapper"]/div[3]/div/div/div[2]/form/div/div[2]/input').send_keys(settings.get_field("password"))
        self.window.find_element_by_xpath('// *[ @ id = "wrapper"] / div[3] / div / div / div[2] / form / button').click()
        sleep(1)

    def get_exam_info(self):
        data = {}
        try:
            sleep(3)
            exam_name = self.window.find_element(By.XPATH, '//*[@id="content-area"]/div[1]/div/div/div[2]/h1').text
        except:
            logger.error('No h1')
            try:
                sleep(5)
                exam_name = self.window.find_element(By.XPATH, '//*[@id="content-area"]/div[1]/div/div/div[2]/h1').text
            except:
                logger.error('No h1_two')
        vendor_name = ''.join(exam_name.split(" ")[0])
        if vendor_name == 'AWS':
            vendor_name = "Amazon"

        data["vendor_name"] = vendor_name
        data["vendor_slug"] = vendor_name.replace(" ", "_").replace("(", "").replace(")", "")
        data["short_name"] = exam_name
        data["exam_long_name"] = exam_name
        data["exam_slug"] = exam_name.replace(" ", "_").replace("(", "").replace(")", "")
        return data


    def get_button(self):
        div = self.window.find_elements(By.CSS_SELECTOR, 'div .testversion')
        lst = []
        for i in div:
            b = i.find_elements(By.CLASS_NAME, 'right')
            for c in b:
                lst.append(c.find_element(By.TAG_NAME, 'button'))
        return lst

    def parse_questions(self, count):
        lst_no_answer = []
        json_elements = {}
        logger.info(count)
        num = 0
        name_exam = self.get_exam_info()['exam_long_name']
        table = []
        for u in range(1, count+1):
            try:
                sleep(5)
                self.get_button()[num].click()
            except:
                logger.error('exam.click()')
                try:
                    sleep(10)
                    self.get_button()[num].click()
                except:
                    logger.error('exam.click() two')
                    continue
            sleep(3)
            WebDriverWait(self.window, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'btn-startQuiz'))
            ).click()
            try:
                modal = self.window.find_element(By.CLASS_NAME, 'modal-content')
            except:
                logger.error("Error modal-content")
                try:
                    sleep(5)
                    modal = self.window.find_element(By.CLASS_NAME, 'modal-content')
                except:
                    logger.error("Error modal-content two")
            try:
                modal.find_element(By.TAG_NAME, 'input').click()
                sleep(2)
                self.window.find_element(By.CLASS_NAME, 'btn-start').click()
            except:
                logger.info('no input')
                sleep(3)
                self.window.find_element(By.CLASS_NAME, 'btn-cancel').click()
                if num >= count:
                    logger.info('Success')

                    self.write_table(f'\n{name_exam}: {str(table)}')
                    return json_elements
                else:
                    self.window.find_element(By.XPATH,
                                             '/html/body/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]').click()
                    num += 1
                    continue
            sleep(4)
            try:
                question_elements = self.window.find_element_by_class_name('attempts-que')
            except:
                logger.error('attempts-que')
                try:
                    sleep(5)
                    question_elements = self.window.find_element_by_class_name('attempts-que')
                except:
                    logger.error('attempts-que two')
            sleep(1)
            all_options = question_elements.find_elements_by_tag_name('li')
            logger.error(all_options)
            for c, i in enumerate(all_options, 1):
                i.click()
                sleep(3)
                button = self.window.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div/div[2]/div[1]/div[2]/div[1]/div[3]/a[2]')
                question_header = f'question_{c}_{num+1}'
                logger.info(question_header)
                question_text = self.window.find_element(By.CSS_SELECTOR, '#root > div > div > div > div > div.container > div.examBlock > div.ExamQuestionsBlock > div.left > div.content > div:nth-child(1)').get_attribute("innerHTML")
                q_t_parts = question_text.replace('<em>', '').replace('</em>', '').replace('<ol>', '').replace('</ol>', '').replace('<h3>', '').replace('</h3>', '').replace('<label>', '').replace('</label>', '').replace('<div>', '').replace('</div>', '').replace('<span>', '').replace('</span>', '').replace('<p>', '').replace('<strong>', '').replace('</strong>', '').replace('<br>', '').replace('<li>', '').replace('</li>', '').replace('</ul>', '').replace('<ul>', '').split("</p>")
                json_elements[question_header] = self.form_json_text(q_t_parts, "question_text", "question_image")
                sleep(1)
            #     # Getting variants of answers
                answer_variants = self.window.find_element(By.CSS_SELECTOR, '.MuiFormControl-root').text
                sleep(1)
                logger.info(answer_variants)
                if answer_variants == '':
                    sleep(1)
                    answer_variants = self.window.find_element(By.XPATH,
                                                               '//*[@id="root"]/div/div/div/div/div[2]/div[1]/div[2]/div[1]/div[2]/fieldset').text
                json_elements[question_header].append({"answer_variants": answer_variants})
                sleep(1)
                try:
                    WebDriverWait(self.window, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'btn-showAnswer'))
                    ).click()
                except:
                    logger.error('mistake btn-showAnswer')
                    lst_no_answer.append(question_header)
                    continue
                    # try:
                    #     self.window.find_element_by_class_name("btn-showAnswer").click()
                    #     sleep(3)
                    # except:
                    #     logger.error('not buuton show answer')
                    #     sleep(3)
                    #     try:
                    #         self.window.find_element_by_class_name("btn-showAnswer").click()
                    #     except:
                    #         for i in range(1, 10):
                    #             if self.window.find_element_by_class_name("btn-showAnswer").click():
                    #                 print(i)
                    #                 print('ok')
                    #                 break
                # try:
                #     self.window.find_element_by_class_name("btn-showAnswer").click()
                #     sleep(3)
                # except:
                #     logger.error('not buuton show answer')
                #     sleep(3)
                #     try:
                #         self.window.find_element_by_class_name("btn-showAnswer").click()
                #     except:
                #         for i in range(1, 10):
                #             if self.window.find_element_by_class_name("btn-showAnswer").click():
                #                 print(i)
                #                 print('ok')
                #                 break
                # sleep(3)
                sleep(1)
                try:
                    # answer_correct = self.window.find_element(By.CSS_SELECTOR, '#root > div > div > div > div > div.container > div.examBlock > div.ExamQuestionsBlock > div.left > div.content > div.explanation-block.show-answer > div:nth-child(4)').get_attribute("innerHTML")
                    answer_correct = WebDriverWait(self.window, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '#root > div > div > div > div > div.container > div.examBlock > div.ExamQuestionsBlock > div.left > div.content > div.explanation-block.show-answer > div:nth-child(4)'))
                    ).get_attribute("innerHTML")
                    logger.info(answer_correct)
                except:
                    logger.info('no answer_correct')
                    try:
                        sleep(5)
                        answer_correct = self.window.find_element(By.CSS_SELECTOR, '#root > div > div > div > div > div.container > div.examBlock > div.ExamQuestionsBlock > div.left > div.content > div.explanation-block.show-answer > div:nth-child(4)').get_attribute("innerHTML")
                    except:
                        logger.info('no answer_correct_two')
                logger.info(answer_correct)
                answer_corrects = answer_correct.replace('</em>', '').replace('<em>', '').replace('</ol>', '').replace('<ol>', '').replace('<p>', '').replace('<strong>', '').replace('</strong>', '').replace('<br>', '').replace('<li>', '').replace('</li>', '').replace('</ul>', '').replace('<ul>', '').split("</p>")
                sleep(1)
                per = self.form_answer_json_text(answer_corrects, "answer_correct_text", "answer_correct_image", "answer_link")
                for i in per:
                    json_elements[question_header].append(i)
                tables = self.window.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div/div[2]/div[1]/div[2]/div[1]/div[2]')
                if tables.get_attribute("innerHTML").find("<table") != -1:
                    table.append(f'question_{c}_{num+1}')

                sleep(3)
                if 'Next' in button.text:
                    continue
                if 'Next' not in button.text:
                    button.click()
                    sleep(1)
                    modal = self.window.find_element(By.CLASS_NAME, 'modal-content')
                    sleep(1)
                    modal.find_element(By.CSS_SELECTOR, 'body > div.MuiDialog-root.modal.modal-exitExam > div.MuiDialog-container.MuiDialog-scrollPaper > div > div.modal-content > div > button.MuiButtonBase-root.MuiButton-root.MuiButton-text.btn.btn-quit').click()
                    WebDriverWait(self.window, 10).until(EC.alert_is_present())
                    self.window.switch_to.alert.accept()
                    sleep(1)
                    self.window.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]').click()
                    num += 1
                    if num >= count:
                    # if num >= 1:
                        logger.info('Success')
                        self.write_table(f'\n{name_exam}: {str(table)}')
                        return json_elements
                    sleep(6)
                    break
        logger.info('Success')

        self.write_table(f'\n{name_exam}: {str(table)}')
        self.write_no_answer(f'\n{name_exam}: {lst_no_answer}')
        logger.info(lst_no_answer)
        return json_elements

    def form_answer_json_text(self, parts, textname, imagename, linkname):
        elements = []
        text_part = ""
        sleep(3)
        logger.info('answer')
        for part in parts:
            if part.find("<a") == -1 and part.find("<img") == -1:
                text_part += part+" "
            if part.find("<a") != -1:
                link = []
                for i in part.split('</a>'):
                    href = self.found_dom_attribute(i, "href")
                    link.append(href)
                elements.append({textname: text_part, linkname: link})
            if part.find("<img") != -1:
                src = self.found_dom_attribute(part, "src")
                elements.append({textname: text_part.replace(part, ''), imagename: src})
                text_part = ""
        if text_part != "" and elements == []:
            elements.append({textname : text_part})
        logger.info(elements)
        return elements


    def form_json_text(self, parts: str, textname: str, imagename: str):
        elements = []
        text_part = ""
        sleep(3)
        for part in parts:
            if part.find("<img") == -1:
                text_part += part+" "
            if part.find("<img") != -1:
                src = self.found_dom_attribute(part, "src")
                elements.append({textname: text_part.replace(part, ' '), imagename: src})
                text_part = ""
        if text_part != "":
            elements.append({textname: text_part})
        return elements

    def write_table(self, text):
        with open('table.txt', 'a') as f:
            f.write("\n" + text)

    def write_no_answer(self, text):
        with open('no_answer.txt', 'a') as f:
            f.write("\n" + text)

    def found_dom_attribute(self,resource,parameter):
        vs = resource.find(parameter+"=\"")
        ve = -1
        for i in range(vs+len(parameter)+2,len(resource)):
            if resource[i] == "\"":
                ve = i
                break
        return resource[vs+len(parameter)+2:ve]
