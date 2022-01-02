from time import sleep
from loguru import logger
import core
lst_link = [
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-303/318',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-304/324'
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-220/356'
    # 'https://www.whizlabs.com/learn/course/microsoft-power-platform-solution-architect-pl600/398',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-dp-203/420',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-dp-100/336',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-ai-102/397',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-400/270'
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-500/279',
    # 'https://www.whizlabs.com/learn/course/microsoft-security-operations-analyst-sc-200/1183',
    # 'https://www.whizlabs.com/learn/course/microsoft-power-functional-consultant-pl-200-certification/359'
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-associate-cloud-engineer/274',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-cloud-architect/239',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-cloud-developer/283',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-cloud-devops-engineer/385',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-cloud-security-engineer/301',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-cloud-network-engineer/294',
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-professional-collaboration-engineer/985',
    # 'https://www.whizlabs.com/learn/course/professional-machine-learning-engineer/394'
    # 'https://www.whizlabs.com/learn/course/google-cloud-certified-cloud-digital-leader/67',
    # 'https://www.whizlabs.com/learn/course/aws-solutions-architect-professional/168/pt',
    # 'https://www.whizlabs.com/learn/course/aws-devops-certification-training/183/pt',
    # 'https://www.whizlabs.com/learn/course/aws-solutions-architect-associate/153/pt',
    # 'https://www.whizlabs.com/learn/course/aws-sysops-administrator-associate/158/pt',
    # 'https://www.whizlabs.com/learn/course/aws-developer-associate/160/pt',
    # 'https://www.whizlabs.com/learn/course/aws-certified-cloud-practitioner/219/pt',
    # 'https://www.whizlabs.com/learn/course/aws-advanced-networking-speciality/195/pt'
    # 'https://www.whizlabs.com/learn/course/aws-certified-big-data-specialty/203/pt',
    # 'https://www.whizlabs.com/learn/course/aws-certified-database-specialty/291/pt',
    # 'https://www.whizlabs.com/learn/course/aws-certified-machine-learning-specialty/281/pt',
    # 'https://www.whizlabs.com/learn/course/aws-certified-security-specialty/231/pt'
    # 'https://www.whizlabs.com/learn/course/designing-microsoft-azure-infrastructure-solutions-az-305/1579',
    # 'https://www.whizlabs.com/learn/course/microsoft-azure-certification-az-204/300'
    # 'https://www.whizlabs.com/learn/course/salesforce-admin-certification/206/pt',
    # 'https://www.whizlabs.com/learn/course/salesforce-platform-app-builder/276'
]
error_links = []
for i in lst_link:
    try:
        logger.info(i)
        settings = core.settings("config.json")
        browser = core.browser(settings)
        worker = core.worker(browser, settings)
        worker.parse_full_exam(i, settings)
        browser.close()
    except Exception as exc:
        logger.error(exc)
        logger.error(i)
        error_links.append(i)
logger.critical(error_links)
