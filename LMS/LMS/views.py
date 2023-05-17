from django.shortcuts import redirect, render
from app.models import Categories, Course, Level, Video, UserCource, Payment
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages
from .settings import *
import razorpay


client = razorpay.Client(auth=(key_id, key_secret))
from time import time
from django.views.decorators.csrf import csrf_exempt


def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status='PUBLISH').order_by('-id')
    context = {
        'category': category,
        'course': course
    }

    return render(request, 'Main/home.html', context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    course = Course.objects.all()
    level = Level.objects.all()
    FreeCourse_count = Course.objects.filter(price=0).count()
    print(FreeCourse_count)
    PaidCourse_count = Course.objects.filter(price__gte=1).count()

    context = {
        'category': category,
        'level': level,
        'course': course,
        'FreeCourse_count': FreeCourse_count,
        'PaidCourse_count': PaidCourse_count
    }
    return render(request, 'Main/single_course.html', context)


def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')
    print(price)

    if price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif price == ['PriceAll']:
        course = Course.objects.all()
    elif category:
        course = Course.objects.filter(category__id__in=category).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in=level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')
    context = {
        'course': course
    }

    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data': t})


def CONTACT_US(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category': category,
    }
    return render(request, 'Main/contact_us.html', context)


def ABOUT_US(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category': category,
    }
    return render(request, 'Main/about_us.html', context)


def SEARCH_COURSE(request):
    query = request.GET['query']
    course = Course.objects.filter(title__icontains=query)
    category = Categories.get_all_category(Categories)

    context = {
        'course': course,
        'category': category,
    }
    return render(request, 'search/search.html', context)


def COURSE_DETAILS(request, slug):
    category = Categories.get_all_category(Categories)
    time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))

    course_id = Course.objects.get(slug=slug)
    try:
        check_enroll = UserCource.objects.get(user=request.user, course=course_id)
    except UserCource.DoesNotExist:
        check_enroll = None
    course = Course.objects.filter(slug=slug)
    if course.exists():
        course = course.first()
    else:
        return redirect('404')
    context = {
        'course': course,
        'category': category,
        'time_duration': time_duration,
        'check_enroll': check_enroll,
    }
    return render(request, 'course/course_details.html', context)


def PAGE_NOT_FOUND(request):
    category = Categories.get_all_category(Categories)
    context = {
        'category': category,
    }
    return render(request, 'error/404.html', context)


def CHECKOUT(request, slug):
    course = Course.objects.get(slug=slug)
    action = request.GET.get('action')
    order = None
    if course.price == 0:
        course = UserCource(
            user=request.user,
            course=course,
        )
        course.save()
        messages.success(request, 'Course Are Success Fully Enrolled!')
        return redirect('my_course')
    elif action == 'create_payment':
        if request.method == "POST":
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            country = request.POST.get('country')
            address_1 = request.POST.get('address_1')
            address_2 = request.POST.get('address_2')
            city = request.POST.get('city')
            status = request.POST.get('status')
            postcode = request.POST.get('postcode')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            order_comments = request.POST.get('order_comments')

            amount = (course.price * 100)
            currency = "INR"
            notes = {
                "name": f'{first_name} {last_name}',
                "country": country,
                "address": f'{address_1} {address_2}',
                "city": city,
                # "state": state,
                "postcode": postcode,
                "phone": phone,
                "email": email,
                "order_comments": order_comments,
            }
            receipt = f"SKOLA-{int(time())}"
            order = client.order.create(
                {
                    'receipt': receipt,
                    'notes': notes,
                    'amount': amount,
                    'currency': currency,
                }
            )
            payment = Payment(
                course=course,
                user=request.user,
                order_id=order.get('id')
            )
            payment.save()
    context = {
        'course': course,
        'order': order,
    }
    return render(request, 'checkout/checkout.html', context)


def MY_COURSE(request):
    category = Categories.get_all_category(Categories)
    course = UserCource.objects.filter(user=request.user)
    discount = UserCource.objects.get

    context = {
        'course': course,
        'discount': discount,
        'category' : category,

    }
    return render(request, 'course/my-course.html', context)


@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_order_id']
            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True
            usercourse = UserCource(
                user=payment.user,
                course=payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()
            context = {
                'data': data,
                'payment': payment,
            }
            return render(request, 'verify_payment/success.html', context)
        except:
            return render(request, 'verify_payment/faild.html')


# def WATCH_COURSE(request, slug):
#     course = Course.objects.filter(slug=slug)
#     lecture = request.GET.get('lecture')
#     video = Video.objects.get(id=lecture)
#     if course.exists():
#         course = course.first()
#     else:
#         return redirect('404')
#
#     context = {
#         'course': course,
#         'video': video,
#     }
#
#     return render(request, 'course/watch-course.html', context)

# def WATCH_COURSE(request, slug):
#     lecture = request.GET.get('lecture')
#     course_id = Course.objects.get(slug=slug)
#     course = Course.objects.filter(slug=slug)
#     try:
#         check_enroll = UserCource.objects.get(user=request.user, course=course_id)
#         video = Video.objects.get(id = lecture)
#         if course.exists():
#             course = course.first()
#         else:
#             return redirect('404')
#     except UserCource.DoesNotExist:
#         return redirect('404')
#
#     context = {
#         'course': course,
#         'video': video,
#         'lecture': lecture,
#
#     }
#     return render(request, 'course/watch_course.html', context)
def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug=slug)
    lecture = request.GET.get('lecture')
    # video = Video.objects.get(id=lecture)

    if course.exists():
        course = course.first()
    else:
        return redirect('404')
    context = {
        'course': course,
        # 'video':video,


    }
    return render(request, 'course/watch-course.html',context)
