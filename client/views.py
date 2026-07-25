from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random

from .models import ClientProfile
from tutor.models import TutorProfile, Skill, Availability
from django.db.models import Q
from django.db.models.functions import Lower
from django.db.models import Count


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Count
from .mock_data import TUTORS 
from tutor.models import Skill

import os
import resend

# Set Resend API key (from environment variables)
resend.api_key = os.getenv("RESEND_API_KEY")


def client_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is None:
            return render(
                request,
                "client/login.html",
                {
                    "email": email,
                    "pass_error": "Invalid email or password"
                }
            )

        # Login successful
        login(request, user)
        request.session["email"] = email
        return redirect("client-dashboard")
        # return redirect("complete-profile")

    return render(request, "client/login.html")


def client_signup(request):
    action = request.POST.get("action")
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        otp = request.POST.get("otp")

        cap=0
        special=['_','@','$']
        sp=0
        num=0

        already_register=User.objects.filter(email=email).exists()

        if not (email.endswith("@gmail.com") 
            or email.endswith("@yahoo.com") 
            or email.endswith("@outlook") 
            or email.endswith("@aol.com") 
            or email.endswith("@hotmail.com") 
            or email.endswith("@zoho.com") 
            or email.endswith("@icloud.com")):
            return render(request, "client/signup.html", 
                          {"email_error": "Please enter a valid email provider",
                           "email": email})
        
        if already_register:
            return render(request, "client/signup.html", 
                          {"email_error": "This email is already registered!",
                           "email": email})

        # STEP 1 — SEND OTP
        # if action == "send_otp":
        #     request.session.pop("otp", None)
        #     generated_otp = otp_generation()
        #     request.session["otp"] = generated_otp
        #     request.session["email"] = email

        #     send_mail(
        #         "SkillLink OTP Verification",
        #         f"Your SkillLink OTP is: {generated_otp}",
        #         "skill.link.connects@gmail.com",
        #         [email],
        #     )

        #     return render(request, "client/signup.html", {
        #         "email": email,
        #         "show_otp": True,
        #         "show_password": False,
        #         "info": "OTP sent successfully"
        #     })
        # STEP 1 — SEND OTP
        if action == "send_otp":
            request.session.pop("otp", None)
            generated_otp = otp_generation()
            request.session["otp"] = generated_otp
            request.session["email"] = email

            # Send OTP using Resend HTTP API
            try:
                resend.Emails.send({
                    "from": "SkillLink <onboarding@resend.dev>",
                    "to": [email],
                    "subject": "SkillLink Client OTP Verification",
                    "html": f"<p>Your SkillLink client verification OTP is: <strong>{generated_otp}</strong></p>"
                })
            except Exception as e:
                return render(request, "client/signup.html", {
                    "email": email,
                    "email_error": f"Failed to send OTP: {str(e)}"
                })

            return render(request, "client/signup.html", {
                "email": email,
                "show_otp": True,
                "show_password": False,
                "info": "OTP sent successfully"
            })
        # STEP 2 — VERIFY OTP
        if action == "verify_otp":
            session_otp = request.session.get("otp")

            if not session_otp or str(otp) != str(session_otp):
                return render(request, "client/signup.html", {
                    "email": email,
                    "show_otp": True,
                    "show_password": False,
                    "otp": otp,
                    "otp_error": "Incorrect OTP"
                })

            return render(request, "client/signup.html", {
                    "email": email,
                    "show_otp": True,
                    "show_password": True,
                    "otp": otp,
                    "otp_success": "OTP verified successfully"})


        if action == "create_account":
            if not password==confirm_password:
                return render(request, "client/signup.html", 
                    {"match_error": "Passcodes do not match",
                    "email": email,
                    "otp": otp,
                    "show_otp": True,
                    "show_password": True,
                    })

            if len(password)<8 or len(password)>12:
                return render(request, "client/signup.html",
                    {"pass_error": "Passcodes must be between the length of 8 to 12 character",
                        "email": email,
                        "otp": otp,
                        "show_otp": True,
                        "show_password": True,})
                
            for i in password:
                if i.isupper():
                    cap+=1
                if i in special:
                    sp+=1
                if i.isdigit():
                    num+=1
            if cap==0:
                return render(request, "client/signup.html",
                    {"pass_error": "Passcodes must contain atleast 1 capital aplhabet",
                        "email": email,
                        "otp": otp,
                        "show_otp": True,
                        "show_password": True,})
            if num==0:
                return render(request, "client/signup.html",
                    {"pass_error": "Passcodes must contain a number",
                        "email": email,
                        "otp": otp,
                        "show_otp": True,
                        "show_password": True,})
            if sp==0:
                return render(request, "client/signup.html",
                    {"pass_error": "Passcodes must contain a special character from _, @, $",
                        "email": email,
                        "otp": otp,
                        "show_otp": True,
                        "show_password": True,})  
            
            User.objects.create_user(
                                        username=email,
                                        email=email,
                                        password=password
                                    )


            # CLEAN SESSION
            request.session.pop("otp", None)

            # return render(request, "core/signup.html", {
            #     "success": "Account created successfully!"
            # })
            request.session["email"] = email
            return redirect("client-dashboard")


    return render(request, "client/signup.html", {
                        "show_otp": False,
                        "show_password": False
                    })


# def otp_generation():
#     x=random.randint(0,10,size=(6,))
#     otp=""
#     for i in x:
#         otp+=str(i)
#     otp=int(otp)
#     return otp
def otp_generation():
    otp = random.randint(100000, 999999)
    return otp


import random

# def send_otp(email):
#     otp = random.randint(100000, 999999)
#     # store otp in session or DB
#     return otp


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Q, Count
from tutor.models import TutorProfile, Skill
from client.models import ClientProfile


@login_required(login_url="client-login")
def client_dashboard(request):

    # ---------- CLIENT PROFILE ----------
    try:
        client_profile = ClientProfile.objects.get(user=request.user)
    except ClientProfile.DoesNotExist:
        return redirect("complete-profile")


    # ---------- SEARCH ----------
    search_query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'skill').lower()

    tutors = TutorProfile.objects.select_related("user").all()

    if search_query:

        if search_by == "name":
            tutors = tutors.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        elif search_by == "skill":
            tutors = tutors.filter(
                skills__name__icontains=search_query
            ).distinct()


    # ---------- SKILL CARDS (CASE-INSENSITIVE, DISTINCT TUTOR COUNT) ----------
    skill_names = Skill.objects.values_list("name", flat=True)

    unique_skill_names = set(name.lower() for name in skill_names)

    skills = []

    for skill_name in unique_skill_names:

        skill_variants = Skill.objects.filter(
            name__iexact=skill_name
        )

        tutor_count = TutorProfile.objects.filter(
            skills__in=skill_variants
        ).distinct().count()

        skill_obj = skill_variants.first()

        if tutor_count > 0 and skill_obj:
            skills.append({
                "id": skill_obj.id,
                "display_name": skill_name.capitalize(),
                "total": tutor_count
            })


    # ---------- CONTEXT ----------
    context = {
        "client": client_profile,
        "tutors": tutors,
        "skills": skills,
        "search_query": search_query,
        "search_by": search_by,
    }


    return render(request, "client/dashboard.html", context)

    
    # try:
    #     client_profile = ClientProfile.objects.get(user=request.user)
    #     # if not client_profile.is_profile_complete:
    #     #     return redirect("complete-profile")
    #     if not client_profile.is_profile_complete:
    #         return redirect("complete-profile")

    # except ClientProfile.DoesNotExist:
        # return redirect('client-login')

    
from django.contrib.auth import logout
from django.shortcuts import redirect

def client_logout(request):
    logout(request)
    return redirect("client-login")

from django.contrib.auth.decorators import login_required



@login_required(login_url="client-login")
def complete_client_profile(request):

    client_profile, _ = ClientProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        client_profile.company_name = request.POST.get("company_name")
        client_profile.location = request.POST.get("location")
        client_profile.bio = request.POST.get("bio")
        client_profile.linkedin = request.POST.get("linkedin")

        if request.FILES.get("proof"):
            client_profile.work_proof = request.FILES.get("proof")

        # SMART CHECK
        if (
            client_profile.company_name and
            client_profile.location and
            client_profile.bio
        ):
            client_profile.is_profile_complete = True
        else:
            client_profile.is_profile_complete = False

        client_profile.save()

        # ✅ ONLY redirect AFTER saving POST
        return redirect("client-dashboard")


    # ✅ GET request → show page
    return render(request, "client/complete_profile.html", {
        "client": client_profile
    })


# for fake data
def skill_detail(request, skill_id):

    skill = Skill.objects.get(id=skill_id)

    search_query = request.GET.get("search", "")

    skill_variants = Skill.objects.filter(
        name__iexact=skill.name
    )

    interns = TutorProfile.objects.filter(
        skills__in=skill_variants
    ).distinct()

    if search_query:
        interns = interns.filter(
            user__first_name__icontains=search_query
        )

    interns = interns.order_by("-rating")

    return render(request, "client/skill_detail.html", {
        "skill": skill,
        "interns": interns,
        "search_query": search_query,
    })

def tutor_profile(request, id):

    USE_FAKE_DATA = False

    if USE_FAKE_DATA:

        tutor = next(
            (t for t in TUTORS if t["id"] == id),
            None
        )

    else:
        tutor_obj = TutorProfile.objects.select_related("user").get(id=id)

        availability = tutor_obj.availabilities.all()
        
        tutor = {
                "id": tutor_obj.id,
                "name": (
                    tutor_obj.user.get_full_name()
                    or tutor_obj.user.first_name
                    or tutor_obj.user.username
                ),
                "bio": tutor_obj.bio or "",
                "skills": tutor_obj.skills.all(),
                "rating": tutor_obj.rating or 0,
                "linkedin_profile": tutor_obj.linkedin_profile or "",
                "github_profile": tutor_obj.github_profile or "",
                "availability": availability,
            }
        return render(request, "client/tutor_profile.html", {
                "tutor": tutor_obj,
                "availability": availability
            })
    return render(request,"client/tutor_profile.html", {
        "tutor": tutor
    })



from .models import HiringRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required


@login_required
def hire_tutor(request, tutor_id):
    
    USE_FAKE_DATA=False
    if USE_FAKE_DATA:
        tutor = next((t for t in TUTORS if t["id"] == tutor_id), None)

    else:
        tutor = get_object_or_404(TutorProfile, id=tutor_id)

    if request.method == "POST":

        skill = request.POST.get("skill")
        budget = request.POST.get("budget")
        duration = request.POST.get("duration")
        mode = request.POST.get("mode")
        description = request.POST.get("description")

        HiringRequest.objects.create(
            client=request.user,
            tutor=tutor,
            skill=skill,
            budget=budget,
            duration=duration,
            mode=mode,
            description=description,
        )

        return redirect("request_success")

    return render(request, "client/hire_tutor.html", {
        "tutor": tutor
    })
def request_success(request):
    return render(request, "client/request_success.html")


@login_required
def my_requests(request):
    requests = HiringRequest.objects.filter(client=request.user).order_by('-created_at')

    return render(request, "client/my_requests.html", {
        "requests": requests
    })
