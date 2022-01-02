import base64
import json
import time

from loguru import logger


import requests
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from openpyxl import Workbook
import sys
import os
from selenium.webdriver.common.by import By


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from twocaptcha import TwoCaptcha

class settings:
    def __init__(self,filename):
        file = open(filename,"r")
        self.fields = json.load(file)
    def get_field(self,fieldname):
        if fieldname in self.fields:
            return self.fields[fieldname]
        else:
            return False

class browser:
    #Настройки браузера подробнее https://peter.sh/experiments/chromium-command-line-switches/
    def __init__(self,settings):
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
        self.window.set_window_size(1200,1000)
    def close(self):
        self.window.close()

class worker:
    def __init__(self,browser,settings):
        self.window = browser.window
        self.settings = settings

    def parse_full_exam(self,link,settings):
        datamassive = {"questions" : {}}
        self.login(settings)
        sleep(2)
        self.window.get(link)
        sleep(2)
        datamassive["exam_info"] = self.get_exam_info()
        json_file_name = self.get_exam_info()['exam_long_name']
        self.window.get(link+"view/1/")
        sleep(2)
        pages = self.get_pages_amount()
        for i in range(pages):
            self.window.get(link+"view/"+str(i+1)+"/")
            try:
                self.window.find_element_by_id("engagement-modal").find_element_by_class_name("btn-secondary").click()
            except:
                pass
            sleep(5)
            self.solve_capcha(settings)
            datamassive["questions"].update(self.parse_questions())
            with open(f"{json_file_name}.json", "w") as stream:
                json.dump(datamassive, stream)


    def get_pages_amount(self):
        return int(self.window.find_element_by_class_name("exam-view-header").find_element_by_class_name("card-text").find_element_by_tag_name("li").text.split(" ")[-2])

    def login(self,settings):
        self.window.get("https://www.examtopics.com/")
        sleep(2)
        self.window.find_element_by_class_name("mr-2").click()
        sleep(2)
        self.window.find_element_by_class_name("username-text").send_keys(settings.get_field("login"))
        self.window.find_element_by_class_name("password-text").send_keys(settings.get_field("password"))
        self.window.find_element_by_class_name("login-button").click()

    def get_exam_info(self):
        data = {}
        logger.info(data)
        if self.window.find_elements_by_class_name("rs-header") != []:
            title = self.window.find_element_by_class_name("sec-spacer").find_element_by_class_name("col-12").text.split(" ")
            description = {}
            fields = self.window.find_element_by_class_name("exam-intro-box").find_elements_by_class_name("row")
            for field in fields:
                try:
                    description[field.find_element_by_class_name("field").text.replace(":","")] = field.find_element_by_class_name("value").text
                except:
                    pass
            if "Certification Provider" in description:
                provider = description["Certification Provider"].split(" ")
                flag = False
                exam_no = -1
                for i in range(len(provider)):
                    if (title[i] != provider[i]):
                        flag = True
                    exam_no = i + 1
                if flag == False:
                    short_name = title[exam_no]
                    if len(provider) >= 1:
                        data["vendor_name"] = description["Certification Provider"]
                        if len(provider) > 1:
                            data["vendor_slug"] = description["Certification Provider"].replace(" ","_").replace("(","").replace(")","")
                    data["short_name"] = short_name
                    data["exam_long_name"] = description["Exam"]
                    data["exam_slug"] = description["Exam"].replace(" ","_").replace("(","").replace(")","")
        return data

    def recapcha_solver(self, settings):
        sleep(10)
        capcha_key = settings.get_field("capcha_key")
        capcha_solve = ""
        win_loc_href = self.window.execute_script("return window.location.href;")
        rcph_key = self.window.find_element_by_class_name("g-recaptcha").get_attribute("data-sitekey")
        rcph_create = requests.get(
            "http://rucaptcha.com/in.php?key=" + capcha_key + "&method=userrecaptcha&googlekey=" + rcph_key + "&pageurl=" + win_loc_href)
        response = rcph_create.text.split("|")
        state = response[0]
        if state == "OK":
            requestid = response[1]
            for i in range(10):
                sleep(15)
                rcph_callback = requests.get(
                    "http://rucaptcha.com/res.php?key=" + capcha_key + "&action=get&id=" + requestid)
                response = rcph_callback.text.split("|")
                state = response[0]
                if state == "OK":
                    capcha_solve = response[1]
                    break
                else:
                    print(state)

        else:
            print(state)

        if capcha_solve != "":
            scripts = self.window.find_elements_by_tag_name("script")
            clear_scripts = []
            for script in scripts:
                if script.get_attribute("type") == "text/javascript":
                    clear_scripts.append(script)
            submit_script = clear_scripts[4].get_attribute("innerHTML").replace(" ", "").replace("\n", "")
            secret_key = self.found_dom_attribute(submit_script, "value")
            self.window.execute_script(
                "$(document.body).append(\"<form action='' method='POST' id='rcph_submit'><input type='hidden' name='csrfmiddlewaretoken' value='" + secret_key + "'><input type='hidden' name='g-recaptcha-response' value='" + capcha_solve + "'></form>\"); $(\"#rcph_submit\").submit();")
            sleep(5)
            if self.window.find_elements_by_class_name("g-recaptcha") == []:
                return True
            else:
                return False

    def image_solver(self, settings):
        cph_key = settings.get_field("capcha_key")
        cph_solve = ""
        cph_imlink = self.window.find_element_by_class_name("captcha").get_attribute("src")
        cph_image = requests.get(cph_imlink).content
        cph_image_64 = base64.b64encode(cph_image).decode("utf-8")
        cph_create = requests.post("http://rucaptcha.com/in.php",
                                   data={"key": cph_key, "body": cph_image_64, "method": "base64"})
        response = cph_create.text.split("|")
        state = response[0]
        if state == "OK":
            requestid = response[1]
            for i in range(10):
                sleep(15)
                rcph_callback = requests.get(
                    "http://rucaptcha.com/res.php?key=" + cph_key + "&action=get&id=" + requestid)
                response = rcph_callback.text.split("|")
                state = response[0]
                if state == "OK":
                    cph_solve = response[1]
                    break
                else:
                    print(state)

        else:
            print(state)
        if cph_solve != "":
            self.window.find_element_by_id("id_captcha_1").send_keys(cph_solve)
            sleep(1)
            self.window.find_element_by_css_selector(".btn.btn-primary").click()

    def solve_capcha(self, settings):
        print("Solving capcha")
        if self.window.find_elements_by_class_name("captcha") != []:
            print("Detected image captcha")
            self.image_solver(settings)
        if self.window.find_elements_by_class_name("g-recaptcha") != []:
            print("Detected google recaptcha")
            self.recapcha_solver(settings)
        else:
            print("No solvable captcha detected")


    # def capcha_solver(self,settings):
    #     rcph_key = self.window.find_element_by_class_name("g-recaptcha").click()
    #     time.sleep(3)
    #     frame_name = self.window.find_element(By.TAG_NAME, 'iframe')
    #     self.window.switch_to_frame(frame_name)
    #     test_two = self.window.find_element(By.TAG_NAME, 'img')
    #     logger.info(test_two)
    #
    #
    #     capcha_key = settings.get_field("capcha_key")
    #     api_key = os.getenv(capcha_key)
    #
    #     solver = TwoCaptcha(api_key, defaultTimeout=120, pollingInterval=5)
    #
    #     try:
    #         result = solver.coordinates('path/to/captcha.jpg',
    #                                     lang='en')
    #         logger.error(result)
    #     except Exception as e:
    #         sys.exit(e)
    #
    #     else:
    #         sys.exit('solved: ' + str(result))

        # capcha_key = settings.get_field("capcha_key")
        # capcha_solve = ""
        # win_loc_href = self.window.execute_script("return window.location.href;")
        # rcph_key = self.window.find_element_by_class_name("g-recaptcha").get_attribute("data-sitekey")
        # rcph_create = requests.get("http://rucaptcha.com/in.php?key="+capcha_key+"&method=hcaptcha&sitekey="+rcph_key+"&pageurl="+win_loc_href)
        # logger.error(rcph_create)
        # response = rcph_create.text.split("|")
        # state = response[0]
        # logger.error(state)
        #
        # if state == "OK":
        #     requestid = response[1]
        #     for i in range(10):
        #         sleep(20)
        #         rcph_callback = requests.get("http://rucaptcha.com/res.php?key="+capcha_key+"&action=get&id="+requestid)
        #         response = rcph_callback.text.split("|")
        #         state = response[0]
        #
        #         if state == "OK":
        #             capcha_solve = response[1]
        #             logger.info(capcha_solve)
        #             break
        #         else:
        #             time.sleep(7)
        #             rcph_create = requests.get(
        #                 "http://rucaptcha.com/in.php?key=" + capcha_key + "&method=hcaptcha&sitekey=" + rcph_key + "&pageurl=" + win_loc_href)
        #             logger.error("http://rucaptcha.com/in.php?key=" + capcha_key + "&method=hcaptcha&sitekey=" + rcph_key + "&pageurl=" + win_loc_href)
        #
        #             response = rcph_create.text.split("|")
        #
        #             if response[0] == 'OK':
        #                 continue
        #
        #
        # else:
        #     print(state)
        
        # if capcha_solve != "":
        #     scripts = self.window.find_elements_by_tag_name("script")
        #     clear_scripts = []
        #
        #     for script in scripts:
        #         if script.get_attribute("type") == "text/javascript":
        #             clear_scripts.append(script)
        #     submit_script = clear_scripts[2].get_attribute("innerHTML").replace(" ","").replace("\n","")
        #     secret_key = self.found_dom_attribute(submit_script,"value")
        #     self.window.execute_script("$(document.body).append(\"<form action='' method='POST' id='rpc_submit'><input type='hidden' name='csrfmiddlewaretoken' value='"+ secret_key +"'><input type='hidden' name='g-recaptcha-response' value='"+ capcha_solve +"'></form>\"); $(\"#rpc_submit\").submit();")
        #     sleep(5)
        #     if self.window.find_elements_by_class_name("g-recaptcha") == []:
        #         return True
        #     else:
        #         return False
            
    def modal(self):
        sleep(10)
        try:
            self.window.find_element(By.CSS_SELECTOR, "#engagement-modal > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > button:nth-child(1)").click()
            logger.info('there modal')
            sleep(2)
        except:
            logger.info('mistake modal')

    def parse_questions(self):
        question_elements = self.window.find_elements_by_class_name("exam-question-card")
        json_elements = {}
        sleep(2)
        self.modal()
        for element in question_elements:
            question_header = "question_"+element.find_element_by_class_name("card-header").text.split("\n")[0].replace("Question #","")+"_"+element.find_element_by_class_name("card-header").text.split("\n")[1].replace("Topic ","")
            question_text = element.find_element_by_class_name("card-text").get_attribute("innerHTML").replace("   ","").strip(" ").split("<br>")
            while "" in question_text:
                question_text.remove("")
            json_elements[question_header] = self.form_json_text(question_text,"question_text","question_image")
            sleep(1)
            element.find_element_by_class_name("reveal-solution").click()
            sleep(1)
            logger.info(question_header)
            # Getting variants of answers
            if element.find_elements_by_class_name("question-choices-container") != []:
                variants = element.find_element_by_class_name("question-choices-container").text
                json_elements[question_header].append({"answer_variants": variants})

            # Getting correct answer
            if element.find_element_by_class_name("correct-answer").get_attribute("innerHTML").find("<img") != -1:
                image_answer = "https://www.examtopics.com" + self.found_dom_attribute(element.find_element_by_class_name("correct-answer").get_attribute("innerHTML"),"src")
                json_elements[question_header].append({"answer_correct_image" : image_answer})
                print("I:",image_answer)
            else:
                text_answer = element.find_element_by_class_name("correct-answer").text
                json_elements[question_header].append({"answer_correct_text" : text_answer})
                print("T:",text_answer)
            if element.find_element_by_class_name("answer-description").text.replace("\n", "") != "":
                answer_correct_text = element.find_element_by_class_name("answer-description").get_attribute("innerHTML").replace("   ","").strip(" ").split("<br>")
                while "" in answer_correct_text:
                    answer_correct_text.remove("")
                json_elements[question_header].extend(self.form_json_text(answer_correct_text,"answer_correct_text","answer_correct_image"))

        return json_elements

    def form_json_text(self,parts,textname,imagename):
        elements = []
        text_part = ""
        logger.info(parts)
        sleep(5)
        for part in parts:
            if part.find("<img") == -1 and part.find("<span") == -1:
                text_part += part+" "
            elif part.find("<img") != -1:
                print(part)
                src = self.found_dom_attribute(part,"src")
                print(src)
                image_part = "https://" + self.window.execute_script("return window.location.host;") + src
                elements.append({textname : text_part, imagename : image_part})
                text_part = ""
        if text_part != "":
            elements.append({textname : text_part})
        return elements
    
    def found_dom_attribute(self,resource,parameter):
        vs = resource.find(parameter+"=\"")
        ve = -1
        for i in range(vs+len(parameter)+2,len(resource)):
            if resource[i] == "\"":
                ve = i
                break
        return resource[vs+len(parameter)+2:ve]