import time
import requests
from playwright.sync_api import sync_playwright

def automate_lab_and_deploy(lab_url, region, qwiklabs_email, qwiklabs_password):
    """
    يفتح رابط المختبر، يضغط Start Lab، يستخرج الحساب المؤقت، وينشر خدمة Cloud Run بالإعدادات الدقيقة المطلوبة.
    """
    with sync_playwright() as p:
        # تشغيل المتصفح بوضع مخفي
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("[*] Opening Qwiklabs / Google Cloud Skills Boost...")
        page.goto(lab_url)
        page.wait_for_load_state("networkidle")

        # تسجيل الدخول إلى منصة Qwiklabs أولاً إذا تطلب الأمر أو إذا تم توفير الحساب
        if qwiklabs_email and qwiklabs_password:
            try:
                if page.locator("text=Sign in").is_visible():
                    page.click("text=Sign in")
                    page.fill('input[type="email"]', qwiklabs_email)
                    page.fill('input[type="password"]', qwiklabs_password)
                    page.click('input[type="submit"]')
                    page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[-] Qwiklabs login bypass or error: {str(e)}")

        # الضغط على زر بدء المختبر تلقائياً
        print("[*] Starting the Lab...")
        start_button = page.locator("text=Start Lab").first
        if start_button.is_visible():
            start_button.click()
            # الانتظار لضمان تخطي أي نافذة منبثقة أو كابتشا وتوليد الحساب
            page.wait_for_timeout(10000) 
        else:
            browser.close()
            return {"success": False, "error": "لم يتم العثور على زر Start Lab في هذه الصفحة."}

        # استخراج بيانات الحساب المؤقت من واجهة المختبر
        try:
            username = page.locator("text=Username").locator("xpath=..").locator(".text-body").text_content().strip()
            password = page.locator("text=Password").locator("xpath=..").locator(".text-body").text_content().strip()
            project_id = page.locator("text=GCP Project ID").locator("xpath=..").locator(".text-body").text_content().strip()
            print(f"[+] Credentials extracted: Project: {project_id}")
        except Exception as e:
            browser.close()
            return {"success": False, "error": f"فشل في استخراج بيانات الحساب المؤقت من الصفحة: {str(e)}"}

        # تسجيل الدخول إلى حساب Google Cloud المؤقت المستخرج
        print("[*] Logging into temporary Google Cloud Account...")
        page.goto("https://google.com")
        page.fill('input[type="email"]', username)
        page.click('#identifierNext')
        page.wait_for_timeout(2000)

        page.fill('input[type="password"]', password)
        page.click('#passwordNext')
        page.wait_for_url("https://google.com**", timeout=60000)

        # الانتقال إلى الكونسول واستخراج الـ Token
        page.goto("https://google.com")
        page.wait_for_timeout(5000)

        # الموافقة على شروط الاستخدام المؤقتة تلقائياً إذا ظهرت
        try:
            if page.locator("text=I agree to the Terms of Service").is_visible():
                page.click('input[type="checkbox"]')
                page.click('text=Agree and Continue')
                page.wait_for_timeout(2000)
        except:
            pass

        # توليد واستخراج رمز الوصول (OAuth Access Token) من كائن المتصفح السحابي
        token = page.evaluate("() => gapi.auth.getToken().access_token")
        browser.close()

        # بناء وإرسال طلب الـ API بالمتطلبات الدقيقة التي حددتها سيدي لـ Cloud Run
        print("[*] Constructing Cloud Run Deployment Request...")
        deploy_url = f"https://googleapis.com{project_id}/locations/{region}/services?serviceId=mustapha35"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # هيكلة الخصائص الفنية الدقيقة (CPU, Memory, Ports, Autoscaling, Timeout)
        payload = {
            "template": {
                "containers": [
                    {
                        "image": "docker.io/winda2635/mustapha-vless-xhttp:latest",
                        "ports": [
                            {
                                "containerPort": 8080
                            }
                        ],
                        "resources": {
                            "limits": {
                                "memory": "1Gi",
                                "cpu": "1"
                            },
                            "cpuIdle": False # تعني أن الـ CPU دائم التخصيص (CPU is always allocated)
                        }
                    }
                ],
                "scaling": {
                    "minInstanceCount": 1,
                    "maxInstanceCount": 16
                },
                "timeout": "3600s", # مدة مهلة الطلب (Request timeout)
                "maxInstanceRequestConcurrency": 1000, # الحد الأقصى للطلبات المتزامنة للحاوية
                "executionEnvironment": "EXECUTION_ENVIRONMENT_GEN2" # الجيل الثاني (Second generation)
            },
            "ingress": "INGRESS_TRAFFIC_ALL" # السماح لكافة اتصالات الدخول (Ingress: All)
        }

        # تنفيذ عملية النشر مباشرة عبر السحابة
        response = requests.post(deploy_url, json=payload, headers=headers)
        
        if response.status_code in:
            res_data = response.json()
            
            # السماح بالوصول العام (Allow public access) عن طريق ضبط الـ IAM للخدمة بشكل تلقائي ومستقل
            set_iam_url = f"https://googleapis.com{project_id}/locations/{region}/services/mustapha35:setIamPolicy"
            iam_payload = {
                "policy": {
                    "bindings": [
                        {
                            "role": "roles/run.viewer",
                            "members": ["allUsers"]
                        },
                        {
                            "role": "roles/run.invoker",
                            "members": ["allUsers"] # جعل الرابط متاح للعامة Unauthenticated
                        }
                    ]
                }
            }
            requests.post(set_iam_url, json=iam_payload, headers=headers)
            
            # استخراج أو بناء رابط الخدمة المتوقع بناءً على المنطقة والمشروع
            generated_url = res_data.get("uri", f"https://mustapha35-{project_id}.run.app (جاري التحضير)")
            return {"success": True, "url": generated_url, "project_id": project_id}
        else:
            return {"success": False, "error": response.text}
