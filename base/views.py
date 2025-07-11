from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

# rooms = [
#     {'id': 1, 'name': 'Lets learn Python'},
#     {'id': 2, 'name': 'Design with Figma'},
#     {'id': 3, 'name': 'Frontend Developers'},
# ]

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Here you would typically authenticate the user
        # For now, we will just redirect to home
        try:
            user = User.objects.get(email=email)  # Fetch the user by email
        except:
            messages.error(request, 'User does not exist')
        user = authenticate(request, email=email,password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password is incorrect')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    # page = 'register'
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')
        
    return render(request, 'base/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    ).distinct()  
    topics = Topic.objects.all()[0:5] 
    room_count = rooms.count()

    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q)
    ).distinct()[:5]  # Get the latest 5 messages related to the search query

    context = {'rooms':rooms, 'topics':topics, 'room_count':room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def room(request,pk):
    # room = None
    # for i in rooms:
    #     if i['id'] == int(pk):
    #         room = i
    room = Room.objects.get(id=pk)  # Fetch the room with the given primary key
    room_messages = room.message_set.all() # Get all messages related to the room
    particiapnts = room.participants.all()  # Get all participants in the room
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,  # Get the currently logged-in user
            room = room,  # Associate the message with the room
            body = request.POST.get('body')  # Get the message body from the POST request
        )
        room.participants.add(request.user)  # Add the user to the room's participants
        return redirect('room', pk=room.id)

    context = {'room':room, 'room_messages':room_messages, 'participants':particiapnts}
    return render(request, 'base/room.html',context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)  # Fetch the user with the given primary key
    rooms = user.room_set.all()  # Get all rooms created by the user
    room_messages = user.message_set.all()  # Get all messages sent by the user
    topics = Topic.objects.all()  # Get all topics
    context = {'user': user, 'rooms': rooms , 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')  # Ensure the user is logged in to create a room
def createRoom(request):
    form = RoomForm()  # Create an instance of the RoomForm
    topics = Topic.objects.all()  # Fetch all topics to display in the form
    if request.method == 'POST':
        topic_name = request.POST.get('topic')  # Get the topic name from the POST request
        topic, created = Topic.objects.get_or_create(name=topic_name)  # Get or create the topic
        form = RoomForm(request.POST)

        Room.objects.create(
            host = request.user,  # Set the host of the room to the currently logged-in user
            topic = topic,  # Associate the room with the topic
            name = request.POST.get('name'),  # Get the room name from the form data
            description = request.POST.get('description')  # Get the room description from the form data
        )

        # if form.is_valid():

        #     room = form.save(commit=False)  # Create a room instance without saving to the database yet
        #     room.host = request.user  # Set the host of the room to the currently logged-in user
        #     room.save() 
            
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)  # Fetch the room to be updated
    form = RoomForm(instance=room)  # Create a form instance with the room data
    topics = Topic.objects.all()  # Fetch all topics to display in the form

    if request.user != room.host :
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')  # Get the topic name from the POST request
        topic, created = Topic.objects.get_or_create(name=topic_name)  # Get or create the topic
        room.name = request.POST.get('name')  # Update the room name
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form':form , 'topics':topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host :
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request,'base/delete.html', {'obj':room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    # Ensure the user is the one who created the message
    # This prevents unauthorized users from deleting messages
    if request.user != message.user:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=message.room.id)
    return render(request,'base/delete.html', {'obj':message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST,request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form': form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)  # Fetch all topics from the database
    return render(request, 'base/topics.html', {'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()[0:4]
    return render(request, 'base/activity.html', {'room_messages': room_messages})