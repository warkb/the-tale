# coding: utf-8
import os
import datetime

from dext.utils.app_settings import app_settings


APP_DIR = os.path.abspath(os.path.dirname(__file__))


accounts_settings = app_settings('ACCOUNTS',
                                 SESSION_REGISTRATION_TASK_ID_KEY='registration_task_id',
                                 FAST_REGISTRATION_USER_PASSWORD='password-FOR_fast-USERS',
                                 FAST_ACCOUNT_EXPIRED_TIME=3*24*60*60,
                                 REGISTRATION_TIMEOUT=1*60,
                                 RESET_PASSWORD_LENGTH=8,
                                 RESET_PASSWORD_TASK_LIVE_TIME=60*60,
                                 CHANGE_EMAIL_TIMEOUT=2*24*60*60,
                                 ACTIVE_STATE_TIMEOUT = 3*24*60*60,
                                 ACTIVE_STATE_REFRESH_PERIOD=3*60*60,
                                 SYSTEM_USER_NICK=u'Смотритель',

                                 ACCOUNTS_ON_PAGE=25,

                                 PREMIUM_EXPIRED_NOTIFICATION_IN=datetime.timedelta(days=3),

                                 NICK_REGEX=u'[a-zA-Z0-9\-\ _а-яА-Я]+',
                                 NICK_MIN_LENGTH=3,
                                 NICK_MAX_LENGTH=30)
