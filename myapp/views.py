from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, Project, ProjectImage, Message, HiringInquiry

# ---------------- LOGIN VIEWS ----------------

def login_page(request):
    return render(request, "myapp/login.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid Admin credentials")
    return render(request, "myapp/admin_login.html")

def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user and not user.is_superuser:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid Student credentials")
    return render(request, "myapp/student_login.html")

@login_required
def user_logout(request):
    logout(request)
    return redirect("login")

# ---------------- DASHBOARD ----------------


from django.db.models import Q

@login_required
def Dashboard(request):
    if request.user.is_superuser:
        # -----------------------------
        # Admin View with recent 3 active students
        # -----------------------------

        # Get search query (optional)
        search_name = request.GET.get('student_name', '').strip()

        # Step 1: Find the 3 most recently active students (those who uploaded projects)
        recent_projects = (
            Project.objects
            .select_related('user')
            .filter(user__is_superuser=False)
            .order_by('-created_at')[:3]
        )

        # Collect unique users from those projects (in order)
        recent_users = []
        seen_user_ids = set()
        for proj in recent_projects:
            if proj.user.id not in seen_user_ids:
                seen_user_ids.add(proj.user.id)
                recent_users.append(proj.user)

        # Step 2: Get Profile objects of those users
        students = Profile.objects.filter(user__in=recent_users).select_related('user')

        # Step 3: Optional search filter (if admin searches, show all matching)
        if search_name:
            students = Profile.objects.filter(
                Q(first_name__icontains=search_name)
                | Q(last_name__icontains=search_name)
                | Q(user__username__icontains=search_name),
                user__is_superuser=False
            ).select_related('user')

        # Step 4: Fetch last 3 projects per student
        student_projects = {}
        for student in students:
            projects = (
                Project.objects
                .filter(user=student.user)
                .prefetch_related('images')
                .order_by('-id')[:3]
            )
            student_projects[student] = projects

        # Step 5: Other stats and messages
        recent_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')[:3]
        unread_count = Message.objects.filter(recipient=request.user, read=False).count()

        total_projects = Project.objects.count()
        total_students = User.objects.filter(is_superuser=False).count()
        total_notifications = Message.objects.filter(recipient=request.user).count()

        context = {
            "is_admin": True,
            "students": students,
            "student_projects": student_projects,
            "recent_messages": recent_messages,
            "unread_count": unread_count,
            "total_projects": total_projects,
            "total_students": total_students,
            "total_notifications": total_notifications,
            "search_name": search_name,
        }
        return render(request, "myapp/dashboard.html", context)


    else:
        # -----------------------------
        # Student View (unchanged)
        # -----------------------------
        profile, created = Profile.objects.get_or_create(user=request.user)

        # Check for incomplete profile
        show_profile_alert = not (profile.first_name and profile.last_name and profile.profile_image)

        # Handle Project Upload
        if request.method == "POST":
            title = request.POST.get("title")
            category = request.POST.get("category")
            description = request.POST.get("description", "")
            tags = request.POST.get("tags", "")
            visibility = request.POST.get("visibility", "Public")
            license = request.POST.get("license", "All Rights Reserved")
            allow_downloads = request.POST.get("allow_downloads") == "on"
            images = request.FILES.getlist("images")

            if title and category and images:
                project = Project.objects.create(
                    user=request.user,
                    title=title,
                    category=category,
                    description=description,
                    tags=tags,
                    visibility=visibility,
                    license=license,
                    allow_downloads=allow_downloads,
                )
                for image in images:
                    ProjectImage.objects.create(project=project, image=image)

                messages.success(request, "Project uploaded successfully!")
                return redirect("dashboard")
            else:
                messages.error(request, "Title, category, and at least one image are required!")

        # Fetch Projects and Messages
        projects = Project.objects.filter(user=request.user).prefetch_related('images').order_by('-id')
        recent_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')[:3]
        unread_count = Message.objects.filter(recipient=request.user, read=False).count()

        total_projects = projects.count()
        total_notifications = Message.objects.filter(recipient=request.user).count()

        context = {
            "is_admin": False,
            "is_student": True,
            "projects": projects,
            "recent_messages": recent_messages,
            "unread_count": unread_count,
            "show_profile_alert": show_profile_alert,
            "total_projects": total_projects,
            "total_notifications": total_notifications,
        }
        return render(request, "myapp/dashboard.html", context)

# ---------------- PROFILE EDIT ----------------

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.first_name = request.POST.get("first_name", "")
        profile.last_name = request.POST.get("last_name", "")
        profile.course = request.POST.get("course", "")
        profile.mobile = request.POST.get("mobile", "")
        profile.location = request.POST.get("location", "")
        profile.address = request.POST.get("address", "")
        profile_image = request.FILES.get("profile_image")
        if profile_image:
            profile.profile_image = profile_image
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("dashboard")

    return render(request, "myapp/edit_profile.html", {"profile": profile})


# ---------------- STUDENT CREATION (ADMIN ONLY) ----------------

@login_required
def create_student(request):
    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, f"Student {username} created successfully!")
            return redirect("dashboard")

    return render(request, "myapp/user_create.html")


# ---------------- VIEW STUDENT PROJECTS ----------------

# @login_required
# def view_student_projects(request, student_id):
#     student = get_object_or_404(Profile, id=student_id)
#     projects = Project.objects.filter(user=student.user).prefetch_related('images')

#     # Calculate total appreciation count
#     total_likes = sum(p.likes.count() for p in projects)

#     return render(
#         request,
#         "myapp/view_student_projects.html",
#         {
#             "student": student,
#             "projects": projects,
#             "profile": student,
#             "total_likes": total_likes,
#         }
#     )
@login_required
def view_student_projects(request, student_id):
    student = get_object_or_404(Profile, id=student_id)
    projects = Project.objects.filter(user=student.user).prefetch_related('images')

    # Total appreciation count (likes)
    total_likes = sum(p.likes.count() for p in projects)
    # Total project views
    total_views = sum(p.views for p in projects)

    return render(
        request,
        "myapp/view_student_projects.html",
        {
            "student": student,
            "projects": projects,
            "profile": student,
            "total_likes": total_likes,
            "total_views": total_views,
        }
    )


# ---------------- MY PROJECTS ----------------

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Profile, Project

@login_required
def my_projects(request):
    if request.user.is_superuser:
        # Admin: see all students and their projects
        students = Profile.objects.filter(user__is_superuser=False).select_related('user')
        student_projects = {}

        # 🔍 Get filter params
        search_name = request.GET.get('name', '').strip()
        search_project = request.GET.get('project', '').strip()
        sort_order = request.GET.get('sort', 'desc')  # 'asc' or 'desc'
        recent_days = request.GET.get('recent_days', '').strip()

        for student in students:
            projects = Project.objects.filter(user=student.user)

            # Filter by project name
            if search_project:
                projects = projects.filter(title__icontains=search_project)

            # Filter by student name
            if search_name:
                if f"{student.first_name} {student.last_name}".lower().find(search_name.lower()) == -1:
                    continue  # Skip this student if not matching

            # Filter by recent days
            if recent_days.isdigit():
                days = int(recent_days)
                since_date = timezone.now() - timedelta(days=days)
                projects = projects.filter(created_at__gte=since_date)

            # Sort
            if sort_order == "asc":
                projects = projects.order_by('created_at')
            else:
                projects = projects.order_by('-created_at')

            projects = projects.prefetch_related('images')
            if projects.exists():
                student_projects[student] = projects

        context = {
            "student_projects": student_projects,
            "search_name": search_name,
            "search_project": search_project,
            "sort_order": sort_order,
            "recent_days": recent_days,
        }
        return render(request, "myapp/projects.html", context)

    else:
        # Student view (no change)
        student, _ = Profile.objects.get_or_create(user=request.user)
        projects_dict = {}

        own_projects = Project.objects.filter(user=request.user).prefetch_related('images').order_by('-id')
        if own_projects.exists():
            projects_dict[student] = own_projects

        other_profiles = Profile.objects.filter(user__is_superuser=False).exclude(user=request.user).select_related('user')
        for other in other_profiles:
            public_projects = Project.objects.filter(user=other.user, visibility="Public").prefetch_related('images').order_by('-id')
            if public_projects.exists():
                projects_dict[other] = public_projects

        return render(request, "myapp/projects.html", {"student_projects": projects_dict})

# ---------------- PROJECT DETAIL ----------------

from django.http import JsonResponse
from .models import Like

# @login_required
# def project_detail(request, pk):
#     project = get_object_or_404(Project.objects.prefetch_related('images'), pk=pk)
#     student = project.user.profile

#     # Handle like/unlike
#     if request.method == "POST" and request.POST.get("action") == "like":
#         like, created = Like.objects.get_or_create(project=project, user=request.user)
#         if not created:
#             like.delete()  # unlike
#         return JsonResponse({
#             "liked": created,
#             "like_count": project.likes.count()
#         })

#     return render(
#         request,
#         "myapp/project_detail.html",
#         {
#             "project": project,
#             "student": student,
#             "is_liked": project.likes.filter(user=request.user).exists(),
#             "like_count": project.likes.count(),
#         }
#     )
@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project.objects.prefetch_related('images'), pk=pk)
    student = project.user.profile

    # Increment view count
    project.views = project.views + 1
    project.save(update_fields=['views'])

    # Handle like toggle (if any)
    if request.method == "POST" and request.POST.get("action") == "like":
        like, created = Like.objects.get_or_create(project=project, user=request.user)
        if not created:
            like.delete()
        return JsonResponse({
            "liked": created,
            "like_count": project.likes.count()
        })

    return render(
        request,
        "myapp/project_detail.html",
        {
            "project": project,
            "student": student,
            "is_liked": project.likes.filter(user=request.user).exists(),
            "like_count": project.likes.count(),
        }
    )


# ---------------- HIRE NOW ----------------
@login_required
def HireNowView(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    student = project.user

    if request.method == "POST":
        hiring_for = request.POST.get("hiring_for")
        categories = request.POST.get("categories")
        budget = request.POST.get("budget")
        description = request.POST.get("description")
        note = request.POST.get("note")
        hiring_type = request.POST.get("hiring_type")

        # ✅ Create the inquiry record
        HiringInquiry.objects.create(
            project=project,
            sender=request.user,
            hiring_for=hiring_for,
            categories=categories,
            budget=budget,
            description=description,
            note=note,
            hiring_type=hiring_type,
        )

        # ✅ Send message only to student
        Message.objects.create(
            project=project,
            sender=request.user,
            recipient=student,
            content=f"{request.user.username} sent a hiring inquiry for your project '{project.title}'."
        )

        # ✅ Appreciation count increment
        try:
            profile = Profile.objects.get(user=student)
            profile.appreciation_count = profile.appreciation_count + 1
            profile.save()
        except Profile.DoesNotExist:
            pass  # If no profile, ignore safely

        messages.success(request, f"Inquiry sent to {student.username} and appreciation added!")
        return redirect("dashboard")

    return render(request, "myapp/hire_form.html", {"project": project, "student": student})

# ---------------- ALL MESSAGES ----------------

# @login_required
# def AllMessagesView(request):
#     all_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
#     all_messages.filter(read=False).update(read=True)
#     return render(request, "myapp/all_messages.html", {"messages": all_messages})
@login_required
def AllMessagesView(request):
    if request.user.is_superuser:
        all_messages = Message.objects.filter(
            recipient=request.user
        ).exclude(sender__is_superuser=True).order_by('-created_at')
    else:
        all_messages = Message.objects.filter(
            recipient=request.user
        ).order_by('-created_at')

    # Mark unread messages as read
    all_messages.filter(read=False).update(read=True)

    # 👇 Use "all_messages" instead of "messages" in render context
    return render(request, "myapp/all_messages.html", {"all_messages": all_messages})
