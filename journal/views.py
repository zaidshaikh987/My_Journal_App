from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.db.models import Count
from datetime import datetime, timedelta, date
import calendar
from .models import User, JournalEntry, Tag, UserProfile
from django.views.decorators.csrf import csrf_exempt
from .models import User, JournalEntry, Tag
from .forms import EntryForm, ChangePasswordCustomForm
from .utils import calculate_longest_streak
from django.utils import timezone
from django.urls import reverse
import calendar

@login_required(login_url="login")
def index(request):
    """
    View for the main calendar page showing the current month's calendar and today's entry.
    """
    # Get current date and timezone-aware today
    today = timezone.now().date()
    
    # Get year and month from query parameters or use current
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        current_date = date(year, month, 1)
    except (ValueError, TypeError):
        current_date = today
        year = current_date.year
        month = current_date.month
    
    # Get first and last day of the month
    first_day = current_date.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Calculate previous and next month for navigation
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
        
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    # Get all entries for the month for the current user
    entries = JournalEntry.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).select_related('user').prefetch_related('tags')
    
    # Create a dictionary of dates with entries for easy lookup
    entries_dict = {entry.date: entry for entry in entries}
    
    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    weeks = []
    
    # Day names for the calendar header
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # Day is not part of the current month
                week_data.append({'day': None, 'entry': None, 'is_today': False})
            else:
                current_date = date(year, month, day)
                is_today = current_date == today
                entry = entries_dict.get(current_date)
                week_data.append({
                    'day': current_date,
                    'entry': entry,
                    'is_today': is_today
                })
        weeks.append(week_data)
    
    # Get today's entry if it exists
    today_entry = JournalEntry.objects.filter(
        user=request.user, 
        date=today
    ).first()
    
    # Get entry counts for stats
    total_entries = JournalEntry.objects.filter(user=request.user).count()
    entries_this_month = entries.count()
    
    return render(request, "journal/index.html", {
        'today': today,
        'today_entry': today_entry,
        'current_month_name': calendar.month_name[month],
        'current_year': year,
        'current_month': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'weeks': weeks,
        'day_names': day_names,
        'total_entries': total_entries,
        'entries_this_month': entries_this_month,
    })
    
    context = {
        'today': today,
        'current_date': current_date,
        'today_entry': today_entry,
        'weeks': weeks,
        'prev_month': prev_month,
        'next_month': next_month,
        'month_name': current_date.strftime('%B %Y'),
    }
    
    return render(request, "journal/index.html", context)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)

            # redirect user to the original page...
            # ...they were trying to access
            next_url = request.POST.get("next")
            print(next_url)
            if next_url:
                return redirect(next_url)

            # default redirect
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.info(request, "Invalid username and/or password.")
            return render(request, "journal/login.html")
    else:
        return render(request, "journal/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            messages.info(request, "Passwords must match.")
            return render(request, "journal/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return render(request, "journal/register.html", {
                "username": username,
                "email": email
            })

        try:
            validate_password(password=password)
        except ValidationError as error:
            messages.error(request, f"{' '.join(error.messages)}")
            return render(request, "journal/register.html", {
                "username": username,
                "email": email
            })
        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.info(request, "Username already taken.")
            return render(request, "journal/register.html")
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "journal/register.html")


@login_required(login_url="login")
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordCustomForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated.")
            return redirect("profile")
        else:
            messages.error(
                request, "Could not update password. Please correct the error(s).")
    else:
        form = ChangePasswordCustomForm(user=request.user)

    return render(request, "journal/change_password.html", {
        "form": form
    })


@require_http_methods(["GET", "POST"])
@login_required(login_url="login")
def create_entry(request, date_str=None):
    # If no date is provided, use today's date
    if not date_str:
        date_str = timezone.now().strftime('%Y-%m-%d')
    
    # Check if entry already exists for this date
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing_entry = JournalEntry.objects.filter(user=request.user, date=entry_date).first()
        if existing_entry:
            messages.warning(request, f"An entry already exists for {entry_date}. Redirecting to edit page.")
            return redirect('update_entry', entry_id=existing_entry.id)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date format.")
        return redirect('index')
    
    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            try:
                # Save the entry
                entry = form.save(commit=False)
                entry.user = request.user
                entry.date = entry_date
                entry.save()
                
                # Handle tags
                tag_names = form.cleaned_data.get("tags", "")
                if tag_names:
                    tag_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
                    for tag_name in tag_list:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        entry.tags.add(tag)
                
                # Update user's streak
                if hasattr(request.user, 'profile'):
                    request.user.profile.update_streak()
                
                messages.success(request, "Entry saved successfully!")
                return redirect('index')
                
            except Exception as e:
                messages.error(request, f"An error occurred while saving your entry: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-fill the form with the date
        form = EntryForm(initial={'date': date_str})
    
    return render(request, "journal/create_entry.html", {
        'form': form,
        'entry_date': entry_date,
        'is_update': False
    })


@login_required(login_url="login")
def update_entry(request, entry_id):
    """
    View for updating an existing journal entry.
    """
    # Get the entry or return 404 if not found
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    if request.method == "POST":
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            try:
                # Save the entry
                updated_entry = form.save(commit=False)
                updated_entry.save()
                
                # Clear existing tags and add new ones
                updated_entry.tags.clear()
                tag_names = form.cleaned_data.get("tags", "")
                if tag_names:
                    tag_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
                    for tag_name in tag_list:
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        updated_entry.tags.add(tag)
                
                messages.success(request, "Entry updated successfully!")
                return redirect('entry_on', date=entry.date.strftime('%Y-%m-%d'))
                
            except Exception as e:
                messages.error(request, f"An error occurred while updating your entry: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize form with entry data
        form = EntryForm(instance=entry)
    
    return render(request, "journal/create_entry.html", {
        'form': form,
        'entry_date': entry.date,
        'is_update': True,
        'entry': entry
    })


@login_required(login_url="login")
def all_entries(request):
    # Query for entries
    try:
        entries = JournalEntry.objects.filter(
            user=request.user)

        month_filter = request.GET.get("month")
        year_filter = request.GET.get("year")
        if month_filter and year_filter:
            month_filter = int(month_filter)
            year_filter = int(year_filter)
            entries = JournalEntry.objects.filter(
                user=request.user, date__month=month_filter, date__year=year_filter)
        # 10 objects per page
        paginator = Paginator(entries, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except:
        messages.error(request, "Could not retrieve data.")
        return render(request, "journal/all_entries.html")

    return render(request, "journal/all_entries.html", {
        "page_entries": page_obj,
    })


@login_required(login_url="login")
def profile(request):
    """
    View to display user profile with statistics and recent activity.
    """
    try:
        # Get all entries for the current user
        entries = JournalEntry.objects.filter(user=request.user).order_by("-date")
        entry_count = entries.count()
        
        # Calculate streaks
        longest_streak = calculate_longest_streak(entries)
        current_streak = 0
        streak_percentage = 0
        
        # Get current streak if there are entries
        if entries.exists():
            today = timezone.now().date()
            last_entry_date = entries.first().date
            
            # If last entry was today or yesterday, check for current streak
            if last_entry_date >= today - timedelta(days=1):
                current_streak = 1
                check_date = last_entry_date - timedelta(days=1)
                
                # Check previous days for consecutive entries
                while True:
                    if entries.filter(date=check_date).exists():
                        current_streak += 1
                        check_date -= timedelta(days=1)
                    else:
                        break
                
                # Calculate streak percentage (capped at 100%)
                streak_percentage = min(100, (current_streak / 30) * 100)  # 30 days as target
        
        # Get recent entries (last 5)
        recent_entries = entries.select_related('user').prefetch_related('tags')[:5]
        
        # Get entry counts for current month
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        entries_this_month = entries.filter(date__month=today.month, date__year=today.year).count()
        entries_today = entries.filter(date=today).count()
        
        # Get date when longest streak was achieved (simplified)
        longest_streak_date = entries.order_by('-date').first().date if entries.exists() else None
        
        context = {
            'entry_count': entry_count,
            'longest_streak': longest_streak,
            'longest_streak_date': longest_streak_date,
            'current_streak': current_streak,
            'streak_percentage': streak_percentage,
            'recent_entries': recent_entries,
            'entries_this_month': entries_this_month,
            'entries_today': entries_today,
            'today': today,
        }
        
        return render(request, "journal/profile.html", context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while loading your profile: {str(e)}")
        return render(request, "journal/profile.html", {
            'entry_count': 0,
            'longest_streak': 0,
            'current_streak': 0,
            'streak_percentage': 0,
            'recent_entries': [],
            'entries_this_month': 0,
            'entries_today': 0,
            'today': timezone.now().date(),
        })

# API


@login_required(login_url="login")
@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
def entry(request, entry_id):
    """
    API endpoint to get, update, or delete a specific journal entry.
    """
    # Get the entry or return 404 if not found
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    if request.method == "GET":
        # Return entry data as JSON
        return JsonResponse({
            "id": entry.id,
            "title": entry.title,
            "content": entry.content,
            "date": entry.date.isoformat(),
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "tags": [tag.name for tag in entry.tags.all()]
        })
        
    elif request.method == "PUT":
        # Update entry
        try:
            data = json.loads(request.body)
            entry.title = data.get('title', entry.title)
            entry.content = data.get('content', entry.content)
            entry.save()
            
            # Update tags if provided
            if 'tags' in data:
                entry.tags.clear()
                for tag_name in data['tags']:
                    tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
                    entry.tags.add(tag)
                    
            return JsonResponse({"status": "success", "message": "Entry updated successfully"})
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    elif request.method == "DELETE":
        # Delete entry
        entry_date = entry.date
        entry.delete()
        return JsonResponse({
            "status": "success", 
            "message": "Entry deleted successfully",
            "redirect": reverse('entry_on', kwargs={'date': entry_date.strftime('%Y-%m-%d')})
        })
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required(login_url="login")
@require_http_methods(["POST"])
def delete_entry(request, entry_id):
    """
    View to handle entry deletion with confirmation.
    """
    # Get the entry or return 404 if not found
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    try:
        # Store the date before deletion for redirect
        entry_date = entry.date
        
        # Delete the entry
        entry.delete()
        
        # Update user's streak if needed
        if entry_date == timezone.now().date():
            # Only update streak if the deleted entry was for today
            user_profile = request.user.userprofile
            user_profile.update_streak()
        
        messages.success(request, "Entry deleted successfully.")
        return redirect('entry_on', date=entry_date.strftime('%Y-%m-%d'))
        
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the entry: {str(e)}")
        return redirect('entry_on', date=entry.date.strftime('%Y-%m-%d'))


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from datetime import datetime
import calendar

@login_required(login_url="login")
def all_entries(request):
    """
    View to display all journal entries with filtering and pagination.
    """
    # Get filter parameters
    month = request.GET.get('month')
    year = request.GET.get('year')
    tag_id = request.GET.get('tag')
    
    # Start with base queryset
    entries = JournalEntry.objects.filter(user=request.user).order_by('-date')
    
    # Apply filters
    filter_applied = False
    if month and month.isdigit() and 1 <= int(month) <= 12:
        entries = entries.filter(date__month=int(month))
        filter_applied = True
    if year and year.isdigit():
        entries = entries.filter(date__year=int(year))
        filter_applied = True
    if tag_id and tag_id.isdigit():
        entries = entries.filter(tags__id=tag_id)
        filter_applied = True
    
    # Get unique years and months for filter dropdowns
    years = JournalEntry.objects.filter(user=request.user).dates('date', 'year', order='DESC')
    years = [y.year for y in years]
    
    # Get all unique tags for the user
    all_tags = Tag.objects.filter(tag_entries__user=request.user).distinct()
    
    # Pagination
    paginator = Paginator(entries, 10)  # Show 10 entries per page
    page = request.GET.get('page')
    
    try:
        page_entries = paginator.page(page)
    except PageNotAnInteger:
        page_entries = paginator.page(1)
    except EmptyPage:
        page_entries = paginator.page(paginator.num_pages)
    
    # Get current date for "Create Entry" button
    today = timezone.now().date()
    
    # Months for dropdown
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    return render(request, 'journal/all_entries.html', {
        'page_entries': page_entries,
        'months': months,
        'years': years,
        'all_tags': all_tags,
        'filter_applied': filter_applied,
        'today': today,
        'current_month': int(month) if month and month.isdigit() and 1 <= int(month) <= 12 else None,
        'current_year': int(year) if year and year.isdigit() else None,
        'current_tag': int(tag_id) if tag_id and tag_id.isdigit() else None,
    })
@require_GET
@login_required(login_url="login")
def entries(request):
    # Query for entries
    try:
        entries = JournalEntry.objects.filter(user=request.user)
    except:
        entries = None
        return JsonResponse({"error": "No entry found."})

    # in order to serialize non-dict objects -> safe=False
    return JsonResponse([entry.serialize() for entry in entries], safe=False)


@login_required(login_url="login")
def entry_on(request, date):
    # Query for the day
    try:
        entry = JournalEntry.objects.get(user=request.user, date=date)
    except JournalEntry.DoesNotExist:
        messages.info(request, "No entry found for this date.")
        return redirect('index')
    
    # Get previous and next entry dates for navigation
    prev_entry = JournalEntry.objects.filter(
        user=request.user, 
        date__lt=entry.date
    ).order_by('-date').first()
    
    next_entry = JournalEntry.objects.filter(
        user=request.user,
        date__gt=entry.date
    ).order_by('date').first()
    
    context = {
        'entry': entry,
        'prev_date': prev_entry.date if prev_entry else None,
        'next_date': next_entry.date if next_entry else None,
    }
    
    return render(request, 'journal/entry_detail.html', context)
