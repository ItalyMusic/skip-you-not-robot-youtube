#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
yt_dlp_bypass_improved.py - تعديل مكتبة yt-dlp لتجاوز مشكلة التحقق من الروبوتات

هذا البرنامج يستخدم تقنية web scraping مع مكتبة yt-dlp لتجاوز مشكلة
"Sign in to confirm you're not a bot" عند تحميل الفيديوهات والصوت من يوتيوب
بدون الحاجة إلى ملفات تعريف الارتباط (cookies).

يستخدم البرنامج عدة تقنيات لتجاوز الحماية:
1. تدوير وكلاء المستخدم (User Agents)
2. محاكاة سلوك الإنسان
3. استخدام selenium لتجاوز التحقق من الروبوتات
4. استخراج روابط الوسائط مباشرة
"""


"""
تم كتابة الأداة كامله بواسطة محمود ايطالي
https://t.me/eg_yp


قناة التطوير
https://t.me/italy_5

"""

import os
import sys
import random
import time
import json
import re
import argparse
import subprocess
from urllib.parse import urlparse, parse_qs

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# قائمة بوكلاء المستخدم المختلفة لتدويرها
USER_AGENTS = [
    # وكلاء مستخدم لمتصفح Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
    
    # وكلاء مستخدم لمتصفح Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/115.0 Mobile/15E148 Safari/605.1.15",
    
    # وكلاء مستخدم لمتصفح Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
]

def get_random_user_agent():
    """
    اختيار وكيل مستخدم عشوائي من القائمة
    """
    return random.choice(USER_AGENTS)

def simulate_human_delay():
    """
    محاكاة تأخير بشري عشوائي
    """
    delay = random.uniform(1.0, 3.0)
    time.sleep(delay)

def is_valid_url(url):
    """
    التحقق من صحة الرابط
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_video_id(url):
    """
    استخراج معرف الفيديو من رابط يوتيوب
    """
    if not is_valid_url(url):
        return None
    
    parsed_url = urlparse(url)
    
    # التعامل مع روابط youtube.com/watch?v=VIDEO_ID
    if parsed_url.netloc in ['youtube.com', 'www.youtube.com'] and parsed_url.path == '/watch':
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            return query_params['v'][0]
    
    # التعامل مع روابط youtu.be/VIDEO_ID
    elif parsed_url.netloc == 'youtu.be':
        return parsed_url.path.lstrip('/')
    
    # التعامل مع روابط youtube.com/shorts/VIDEO_ID
    elif parsed_url.netloc in ['youtube.com', 'www.youtube.com'] and '/shorts/' in parsed_url.path:
        return parsed_url.path.split('/shorts/')[1]
    
    return None

def install_required_packages():
    """
    تثبيت الحزم المطلوبة إذا لم تكن موجودة
    """
    if not SELENIUM_AVAILABLE:
        print("تثبيت الحزم المطلوبة...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
            print("تم تثبيت الحزم بنجاح. يرجى إعادة تشغيل البرنامج.")
            sys.exit(0)
        except Exception as e:
            print(f"فشل تثبيت الحزم: {str(e)}")
            sys.exit(1)

def setup_selenium_driver():
    """
    إعداد متصفح Selenium
    """
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # إخفاء أنه متصفح آلي
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_video_info_with_selenium(url, verbose=False):
    """
    استخراج معلومات الفيديو باستخدام Selenium
    """
    if verbose:
        print("استخراج معلومات الفيديو باستخدام Selenium...")
    
    driver = setup_selenium_driver()
    
    try:
        driver.get(url)
        
        # محاكاة سلوك الإنسان
        simulate_human_delay()
        
        # التمرير لأسفل لتحميل المزيد من المحتوى
        driver.execute_script("window.scrollBy(0, 500)")
        
        # انتظار تحميل الفيديو
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
        except TimeoutException:
            if verbose:
                print("لم يتم العثور على عنصر الفيديو")
        
        # استخراج البيانات من صفحة الويب
        page_source = driver.page_source
        
        # البحث عن بيانات الفيديو في JavaScript
        js_data = re.search(r'var ytInitialPlayerResponse\s*=\s*({.+?});', page_source)
        if js_data:
            json_str = js_data.group(1)
            try:
                data = json.loads(json_str)
                
                # استخراج روابط الوسائط
                formats = []
                if 'streamingData' in data and 'formats' in data['streamingData']:
                    formats.extend(data['streamingData']['formats'])
                if 'streamingData' in data and 'adaptiveFormats' in data['streamingData']:
                    formats.extend(data['streamingData']['adaptiveFormats'])
                
                # استخراج معلومات الفيديو
                video_info = {
                    'title': data.get('videoDetails', {}).get('title', 'Unknown Title'),
                    'formats': formats
                }
                
                return video_info
            except json.JSONDecodeError:
                if verbose:
                    print("فشل تحليل بيانات JSON")
        
        return None
    
    finally:
        driver.quit()

def download_with_direct_url(url, output_path=None, verbose=False):
    """
    تحميل الفيديو باستخدام الرابط المباشر
    """
    if verbose:
        print(f"تحميل الفيديو من الرابط المباشر: {url}")
    
    cmd = ["wget", "-O"]
    
    if output_path:
        cmd.append(output_path)
    else:
        cmd.append("output.mp4")
    
    cmd.append(url)
    
    try:
        if verbose:
            print(f"تنفيذ الأمر: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # عرض التقدم في الوقت الفعلي
        for line in process.stdout:
            print(line, end='')
        
        # انتظار انتهاء العملية
        process.wait()
        
        # التحقق من نجاح العملية
        if process.returncode != 0:
            error_output = process.stderr.read()
            print(f"فشل التحميل مع رمز الخطأ: {process.returncode}")
            print(f"رسالة الخطأ: {error_output}")
            return False
        
        return True
    
    except Exception as e:
        print(f"حدث خطأ أثناء التحميل: {str(e)}")
        return False

def download_with_yt_dlp_fallback(url, output_format="best", audio_only=False, output_path=None, verbose=False):
    """
    محاولة التحميل باستخدام yt-dlp كحل احتياطي
    """
    if verbose:
        print("محاولة التحميل باستخدام yt-dlp كحل احتياطي...")
    
    # تحضير الأمر مع خيارات مختلفة
    cmd = ["yt-dlp"]
    
    # استخدام وكيل مستخدم
    user_agent = get_random_user_agent()
    cmd.extend(["--user-agent", user_agent])
    
    # إضافة خيارات إضافية لتجاوز الحماية
    cmd.extend([
        "--sleep-interval", "5", 
        "--max-sleep-interval", "10",
        "--geo-bypass",
        "--ignore-errors",
        "--no-check-certificates",
        "--prefer-insecure",
        "--no-cache-dir",
        "--rm-cache-dir",
        "--extractor-retries", "5",
        "--fragment-retries", "5",
        "--skip-unavailable-fragments",
        "--force-ipv4"
    ])
    
    # إضافة خيارات لتحميل الصوت فقط إذا تم تحديد ذلك
    if audio_only:
        cmd.extend(["-f", "bestaudio"])
        if output_format.lower() == "mp3":
            cmd.extend(["--extract-audio", "--audio-format", "mp3"])
    else:
        cmd.extend(["-f", output_format])
    
    # إضافة مسار الإخراج إذا تم تحديده
    if output_path:
        cmd.extend(["-o", output_path])
    
    # إضافة خيار العرض التفصيلي إذا تم تحديده
    if verbose:
        cmd.append("-v")
    
    # إضافة الرابط
    cmd.append(url)
    
    # محاكاة تأخير بشري
    simulate_human_delay()
    
    # تنفيذ الأمر
    try:
        if verbose:
            print(f"تنفيذ الأمر: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # عرض التقدم في الوقت الفعلي
        for line in process.stdout:
            print(line, end='')
        
        # انتظار انتهاء العملية
        process.wait()
        
        # التحقق من نجاح العملية
        if process.returncode != 0:
            error_output = process.stderr.read()
            print(f"فشل التحميل مع رمز الخطأ: {process.returncode}")
            print(f"رسالة الخطأ: {error_output}")
            return False
        
        return True
    
    except Exception as e:
        print(f"حدث خطأ أثناء التحميل: {str(e)}")
        return False

def download_youtube_video(url, output_format="best", audio_only=False, output_path=None, verbose=False):
    """
    تحميل فيديو يوتيوب باستخدام تقنية web scraping
    
    المعلمات:
        url (str): رابط الفيديو
        output_format (str): صيغة الإخراج
        audio_only (bool): تحميل الصوت فقط
        output_path (str): مسار الإخراج
        verbose (bool): عرض معلومات تفصيلية
    
    العائد:
        bool: نجاح أو فشل التحميل
    """
    if not is_valid_url(url):
        print(f"خطأ: الرابط '{url}' غير صالح")
        return False
    
    # التأكد من تثبيت الحزم المطلوبة
    if not SELENIUM_AVAILABLE:
        install_required_packages()
        # بعد التثبيت، يجب إعادة استيراد المكتبات
        global webdriver, Options, Service, By, WebDriverWait, EC, TimeoutException, NoSuchElementException
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
    # استخراج معلومات الفيديو باستخدام Selenium
    video_info = extract_video_info_with_selenium(url, verbose)
    
    if video_info and 'formats' in video_info and video_info['formats']:
        # اختيار الصيغة المناسبة
        selected_format = None
        
        if audio_only:
            # البحث عن أفضل صيغة صوتية
            audio_formats = [f for f in video_info['formats'] if f.get('audioQuality') and not f.get('qualityLabel')]
            if audio_formats:
                selected_format = max(audio_formats, key=lambda x: int(x.get('bitrate', 0)))
        else:
            # البحث عن أفضل صيغة فيديو
            video_formats = [f for f in video_info['formats'] if f.get('qualityLabel')]
            if video_formats:
                selected_format = max(video_formats, key=lambda x: int(x.get('width', 0) * x.get('height', 0)))
        
        if selected_format and 'url' in selected_format:
            # تحديد اسم الملف الافتراضي إذا لم يتم تحديده
            if not output_path:
                title = video_info.get('title', 'video').replace(' ', '_')
                ext = 'mp3' if audio_only and output_format.lower() == 'mp3' else 'mp4'
                output_path = f"{title}.{ext}"
            
            # تحميل الفيديو باستخدام الرابط المباشر
            return download_with_direct_url(selected_format['url'], output_path, verbose)
    
    # إذا فشل استخراج الرابط المباشر، استخدم yt-dlp كحل احتياطي
    print("لم يتم العثور على رابط مباشر للتحميل. جاري استخدام yt-dlp كحل احتياطي...")
    return download_with_yt_dlp_fallback(url, output_format, audio_only, output_path, verbose)

def main():
    """
    الدالة الرئيسية للبرنامج
    """
    parser = argparse.ArgumentParser(description="تحميل فيديوهات وصوت من يوتيوب مع تجاوز التحقق من الروبوتات")
    parser.add_argument("url", help="رابط الفيديو")
    parser.add_argument("-f", "--format", default="best", help="صيغة الإخراج (الافتراضي: best)")
    parser.add_argument("-a", "--audio-only", action="store_true", help="تحميل الصوت فقط")
    parser.add_argument("-o", "--output", help="مسار الإخراج")
    parser.add_argument("-v", "--verbose", action="store_true", help="عرض معلومات تفصيلية")
    
    args = parser.parse_args()
    
    success = download_youtube_video(
        args.url, 
        args.format, 
        args.audio_only, 
        args.output, 
        args.verbose
    )
    
    if success:
        print("تم التحميل بنجاح!")
        return 0
    else:
        print("فشل التحميل.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
