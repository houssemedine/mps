from asyncio import to_thread
from distutils.command.install_egg_info import to_filename
from itertools import cycle, groupby
from operator import index
from queue import Empty
from django.http import HttpResponse
from django.shortcuts import render ,redirect ,get_object_or_404
from app.models import Division,Material,HolidaysCalendar,Product,WorkData,CalendarConfigurationTreatement,CalendarConfigurationCpordo,Coois,Zpp,Shopfloor,Cycle
from app.forms import DivisionForm,MaterialForm,ProductForm,CalendarConfigurationCpordoForm,CalendarConfigurationTreatementForm 
from datetime import  date, datetime, timedelta, time, timezone
from io import StringIO
import psycopg2, pandas as pd
import numpy as np
from django.contrib import messages
from app.decorators import allowed_users
import random
from dateutil.relativedelta import relativedelta




# Create your views here.
#Comment Houssem
#Comment Marwa
#*********************CRUD Division************************

# add new object(Division)
def create_division(request):
    form = DivisionForm(request.POST)
    if request.method == "POST" :
        if form.is_valid():
            form.save()
            messages.success(request,"Division created successfully!")
        else:
            messages.error(request,"Division exit or Form not valid! try again")
    return redirect(read_division)


# read all objects(Division)
def read_division(request): 
    #get Division form
    form = DivisionForm()
    # undeleted_objects object of soft delete manager
    data = Division.objects.all().order_by('id')  
    return render(request, "app/division/home_division.html", {'data':data,'form':form})


#update object(Division) by id
def update_division(request):
    #get id
    id = id = request.POST.get('id')
    # fetch the object related to passed id
    obj = get_object_or_404(Division, id = id)
    # pass the object as instance in form
    form = DivisionForm(request.POST or None, instance = obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request,"Division updated successfully!")
        else:
            messages.error(request,"try again!")
                
    return redirect("./")


# delete object(Division) by id
def delete_division(request, id):
    # fetch the object related to passed id
    obj = get_object_or_404(Division, id = id)
    # delete object
    obj.soft_delete()
    #alert message
    messages.success(request,"Division deleted successfully!")
    return redirect("../")
    

# restore object(Division) by id
def restore_division(request, id):
    # fetch the object related to passed id
    obj = get_object_or_404(Division, id = id)
    # restore object
    obj.restore() 
    #alert message
    messages.success(request,"Division restored successfully!")
    return redirect("../")
    

#*********************CRUD Material************************

# add new object(Material)
def create_material(request,division,product):
    form = MaterialForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            instance=form.save(commit=False)
            instance.product_id=product
            instance.save()
            messages.success(request," Material created successfully!")
        else:
            messages.error(request,"Form not valid! try again")          
    return redirect(f'../{product}/material/')


# read all objects(Material)
def read_material(request):
    # undeleted_objects object of soft delete manager
    data = Material.objects.all().order_by('id')    
    return render(request, "app/material/materials.html", {'data':data})


#update object(Material) by id
def update_material(request,division):
    #get id
    id = id = request.POST.get('id')
    # fetch the object related to passed id
    obj = get_object_or_404(Material, id = id)
    # pass the object as instance in form
    form = MaterialForm(request.POST or None, instance = obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request,"Material updated successfully!")
        else:
            messages.error(request,"try again!")    
    return redirect(f'./{str(obj.product_id)}/material/')
    

# delete object (Material) by id
def delete_material(request, division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(Material, id = id)
    # delete object
    obj.soft_delete()
    #alert message
    messages.success(request,"Material deleted successfully!")
    return redirect(f'../{str(obj.product_id)}/material/')
   

# restore object(Material) by id
def restore_material(request, division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(Material, id = id)
    # restore object
    obj.restore()
    #alert message
    messages.success(request,"Material restored successfully!")
    return redirect(f'../{str(obj.product_id)}/material/')    


# find all Material for product 
def material(request ,division, product):
    #get MaterialForm
    form = MaterialForm()
    # undeleted_objects object of soft delete manager
    data = Material.objects.filter(product__pk = product ).order_by('id')    
    return render(request, "app/material/material.html", {'data':data,'division':division,'product':product,'form':form})


#******************** calendar****************************
def calendar(request,division,product):
    #get smooth family from product
    smooth_family= Material.undeleted_objects.filter(product_id = product).values('Smooth_Family').distinct().order_by('Smooth_Family')
    # print('**********')
    print(smooth_family)
    # get cycle objects
    cycle=Cycle.undeleted_objects.all().filter(product_id = product, owner = 'officiel')
    #material_data=Material.undeleted_objects.filter(product_id = product).values('Smooth_Family').distinct().order_by('Smooth_Family')
    # get product object to display in calendar
    products_data= Product.undeleted_objects.all()
    # get all work data objects to display in Calendar
    workdata = WorkData.undeleted_objects.all().filter(product_id = product, owner = 'officiel')
    # get all holiday objects to display in Calendar
    holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product, owner = 'officiel') 
    # get cycle ifo and workdata infos to display in Calendar
    #workdata=WorkData.objects.values('cycle__cycle_time','cycle__id','id','startTime','endTime','date','FTEhourByDay','ExtraHour','Absenteeism_ratio','Unproductiveness_ratio','Efficienty_ratio').filter(product_id = product, owner = 'officiel') 
    return render(request, "app/calendar/calendar.html",{'product':product,'division':division,'holidays':holidays,'workdata':workdata,'products_data':products_data,'smooth_family': smooth_family,'cycle': cycle})


# create calendar for product 
def create_calendar(request,division,product):
    # get list of days from dataBase to compare if exist 
    days = list(HolidaysCalendar.objects.values_list('holidaysDate',flat=True))
    # get list of product_id from database to compare if exist
    products =list(HolidaysCalendar.objects.values_list('product_id',flat=True))
    if request.method=='POST' and 'save-event' in request.POST:
        # get inputs values
        id = request.POST.get('event-index')
        name = request.POST.get('event-name')
        startDate = request.POST.get('event-start-date')
        endDate = request.POST.get('event-end-date')
        # If id exist Update Object if not create new one
        if id:
            #get object HolidaysCalendar
            #first : to get object not queryset 
            holiday=HolidaysCalendar.objects.all().filter(id=id).first()  #intilisation object
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                #update attributes values with new values
                holiday.holidaysDate= startDate
                holiday.name=name
                #save
                holiday.save()
        else:
        # add one day in database
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                # check if day and product_id exists in DB don't save else save
                if (startDate.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days] ) and (int(product) in products):
                    exist_day =HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = startDate,product_id =product) 
                    exist_day.delete()
                    data = HolidaysCalendar(name=name,holidaysDate=startDate,product_id =product)
                    data.save()
                else:
                    # delete workdata
                    exist_on_days = WorkData.undeleted_objects.all().filter(date = startDate,product_id =product) 
                    exist_on_days.delete()
                    # delete cycle with date and product_id
                    exist_cycle=Cycle.undeleted_objects.all().filter(work_day = startDate,product_id =product)
                    exist_cycle.delete()
                    data = HolidaysCalendar(name=name,holidaysDate=startDate,product_id =product)
                    data.save()
            # add list of days in database       
            else: 
                startDate=datetime.strptime(startDate,'%m/%d/%Y')
                endDate=datetime.strptime(endDate,'%m/%d/%Y')
                delta= endDate-startDate
                day=""
                for i in range(delta.days+1):
                    day= startDate + timedelta(days=i)
                    print(day)
                    # check if day and product_id exists in DB don't save else save
                    if (day.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days]) and (int(product) in products):
                        exist_day =HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = day,product_id =product) 
                        exist_day.delete()
                        data = HolidaysCalendar(name=name,holidaysDate=day,product_id =product)
                        data.save()
                    else :
                        exist_on_days = WorkData.undeleted_objects.all().filter(date = day,product_id =product) 
                        exist_on_days.delete()
                        # delete cycle with date and product_id
                        exist_cycle=Cycle.undeleted_objects.all().filter(work_day = day,product_id =product)
                        exist_cycle.delete()
                        data = HolidaysCalendar(name=name,holidaysDate=day,product_id =product)
                        data.save()
    return redirect("../calendar")


# delete day (holiday or workdata and cycle)
def delete_day(request,division,product): 
    #holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product)
    if request.method =="POST"  and 'delete' in request.POST:
        # get id value from form
        id = request.POST.get('date_id')
        # get name from form 
        date_type = request.POST.get('date_type')
        #get cycle id from form
        cycle_id = request.POST.getlist('cycle_id')
        # get cycle object by id 
        for i in cycle_id:
            obj_cycle = get_object_or_404(Cycle, id = i)
            # delete cycle object
            obj_cycle.soft_delete()
        model = WorkData if date_type=='Work Day' else HolidaysCalendar
        obj = get_object_or_404(model, id = id)
        # delete object
        obj.soft_delete()
        # redirect to calendar 
    return redirect("../calendar")
    #return render(request,"app/calendar/calendar.html",{'product':product} )
    
#********************Custom calendar****************************

#duplicate calendar : 
# delete old data( holidayscalendar, workdata, cycle) and get data from calendar and save new data
def duplicate_calendar(request,division,product):
    #Delete custom holidays
    custom_holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product,owner = 'marwa')
    custom_holidays.delete()
    ##Delete custom workday
    work = WorkData.undeleted_objects.all().filter(product_id = product,owner = 'marwa')
    work.delete()
    # delete custom cycle 
    cycle = Cycle.undeleted_objects.all().filter(product_id = product,owner = 'marwa')
    cycle.delete()
    #save data for loop holidays
    holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product)
    for data in holidays:
        custom_holidays = HolidaysCalendar(name=data.name,holidaysDate=data.holidaysDate,product_id =data.product_id,owner = 'marwa')
        custom_holidays.save()
    #save data for loop work
    work = WorkData.undeleted_objects.all().filter(product_id = product)  
    for data in work:
        custom_work_data = WorkData(date=data.date,startTime=data.startTime,endTime=data.endTime,FTEhourByDay=data.FTEhourByDay,ExtraHour=data.ExtraHour,Absenteeism_ratio=data.Absenteeism_ratio,Unproductiveness_ratio=data.Unproductiveness_ratio,Efficienty_ratio=data.Efficienty_ratio,product_id =data.product_id,owner = 'marwa')
        custom_work_data.save()
        # get cycle object with product_id and workdata_id 
        cycles = Cycle.undeleted_objects.all().filter(product_id = product, workdata_id=data.id) 
        # save cycle with new value of workdata_id 
        for cycle in cycles:
            custom_cycle= Cycle(work_day=cycle.work_day,division=cycle.division,profit_center=cycle.profit_center,smooth_family=cycle.smooth_family,cycle_time=cycle.cycle_time, workdata_id=custom_work_data.id,product_id = product, owner = 'marwa')
            custom_cycle.save()
    #call function create new holiday object        
    create_custom_calendar(request,division,product)
    #call function create new work data object 
    custom_work(request,division,product)
    return redirect("../customcalendar")
    #return render(request,"app/calendar/custom_calendar.html", {'product':product,'holidays':custom_holidays})

#custom calendar
def custom_calendar(request,division,product):
    #get smooth family
    smooth_family= Material.undeleted_objects.filter(product_id = product).values('Smooth_Family').distinct().order_by('Smooth_Family')
    print('**************',smooth_family)
    #  get cycle data objects
    cycle= Cycle.undeleted_objects.all().filter(product_id = product ,owner = 'marwa')
    # material_data=Material.undeleted_objects.filter(product_id = product).values('Smooth_Family').distinct().order_by('Smooth_Family')
    # get all holiday objects to display in Calendar
    holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product , owner = 'marwa') 
    # get all work data objects to display in Calendar    
    work = WorkData.undeleted_objects.all().filter(product_id = product ,owner = 'marwa')
    return render(request,"app/calendar/custom_calendar.html",{'product':product,'division':division,'holidays':holidays,'work':work,'smooth_family': smooth_family,'cycle':cycle})
    

#create custom calendar
def create_custom_calendar(request,division,product):
    # get list of days from dataBase to compare if exist 
    days = list(HolidaysCalendar.objects.values_list('holidaysDate',flat=True))
    # get list of product_id from database to compare if exist
    products =list(HolidaysCalendar.objects.values_list('product_id',flat=True)) 
    if request.method=='POST' and 'save-event' in request.POST:
        # get inputs values
        id = request.POST.get('event-index')
        owner = request.POST.get('owner')
        name = request.POST.get('event-name')
        startDate = request.POST.get('event-start-date')
        endDate = request.POST.get('event-end-date')
        # If id exist Update Object if not create new one
        if id:
            #get object work data
            #first : to get object not queryset 
            holiday=HolidaysCalendar.objects.all().filter(id=id).first()  #intilisation object
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                #update attributes values with new values
                holiday.holidaysDate= startDate
                holiday.name=name
                #save
                holiday.save()
                return redirect("../customcalendar")
        else:
            # add one day in database
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                # check if day and product_id exists in DB don't save else save
                if (startDate.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days] ) and (int(product) in products):
                    exist_day =HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = startDate,product_id =product,owner = 'marwa') 
                    exist_day.delete()
                    data = HolidaysCalendar(name=name,holidaysDate=startDate,product_id =product, owner = owner)
                    data.save()
                else:
                    exist_on_days = WorkData.undeleted_objects.all().filter(date = startDate,product_id =product,owner = 'marwa') 
                    exist_on_days.delete()
                    exist_cycle=Cycle.undeleted_objects.all().filter(work_day = startDate,product_id =product,owner = 'marwa')
                    exist_cycle.delete()
                    data = HolidaysCalendar(name=name,holidaysDate=startDate,product_id =product, owner = owner)
                    data.save()
            # add list of days in database       
            else: 
                startDate=datetime.strptime(startDate,'%m/%d/%Y')
                endDate=datetime.strptime(endDate,'%m/%d/%Y')
                delta= endDate-startDate
                day=""
                for i in range(delta.days+1):
                    day= startDate + timedelta(days=i)
                    # check if day and product_id exists in DB don't save else save
                    if (day.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days]) and (int(product) in products):
                        #delete exist data and save new objects
                        exist_day =HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = day,product_id =product, owner = 'marwa') 
                        exist_day.delete()
                        data = HolidaysCalendar(name=name,holidaysDate=day,product_id =product, owner = owner)
                        data.save()   
                    else :
                        exist_on_days = WorkData.undeleted_objects.all().filter(date = day,product_id =product,owner = 'marwa') 
                        exist_on_days.delete()
                        exist_cycle=Cycle.undeleted_objects.all().filter(work_day = day,product_id =product,owner = 'marwa')
                        exist_cycle.delete()
                        data = HolidaysCalendar(name=name,holidaysDate=day,product_id =product, owner = owner)
                        data.save()    
    return redirect("../customcalendar")


# delete day (holiday or work) for custom
def delete_day_custom(request,division,product):  # sourcery skip: avoid-builtin-shadow
    #holidays = HolidaysCalendar.undeleted_objects.all().filter(product_id = product)
    if request.method =="POST"  and 'delete-custom' in request.POST:
        # get id value from form
        id = request.POST.get('date_id')
        date_type = request.POST.get('date_type')
        #get cycle id from form
        cycle_id = request.POST.getlist('cycle_id')
        #get cycle object by id
        for i in cycle_id:
            obj_cycle = get_object_or_404(Cycle, id = i)
            # delete object
            obj_cycle.soft_delete()
        model = WorkData if date_type=='Work Day' else HolidaysCalendar
        obj = get_object_or_404(model, id = id)
        # delete object
        obj.soft_delete()
        # redirect to calendar 
    return redirect("../customcalendar")

#********************Crud Product****************************
# add new object(product)
def create_product(request,division):
    form = ProductForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
         instance=form.save(commit=False)
         instance.division_id=division
         instance.save()
         messages.success(request," Product created successfully!")
        else:
            messages.error(request,"Form not valid! try again") 
    return redirect(f'../{division}/product/')
   

#update object(Product) by id
def update_product(request):
    id = id = request.POST.get('id')
    # fetch the object related to passed id
    obj = get_object_or_404(Product, id = id)
    # pass the object as instance in form
    form = ProductForm(request.POST or None, instance = obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request," Product updated successfully!")  
        else:
            messages.error(request," try again!")        
    return redirect(f'./{str(obj.division_id)}/product/')
    

# delete object(Product) by id
def delete_product(request, id):
    # fetch the object related to passed id
    obj = get_object_or_404(Product, id = id)
    # delete object
    obj.soft_delete()
    messages.success(request," Product deleted successfully!")  
    return redirect(f'../{str(obj.division_id)}/product/')
    

# restore object(Product) by id
def restore_product(request, id):
    # fetch the object related to passed id
    obj = get_object_or_404(Product, id = id)
    # restore object
    obj.restore()
    messages.success(request," Product restored successfully!")  
    return redirect(f'../{str(obj.division_id)}/product/')


# find all product for division 
def product(request ,division):
    form = ProductForm()
    # undeleted_objects object of soft delete manager
    data = Product.objects.filter(division__pk = division ).order_by('id')    
    return render(request, "app/product/product.html", {'data':data,'division':division,'form':form})

#********************work Data***********************************
#create work data for calendar
def work_data(request,division,product):
    work = WorkData.undeleted_objects.all().filter(product_id = product) 
    # get list of days from dataBase to compare if exist 
    days = list(work.values_list('date',flat=True))
    # get list of product_id from database to compare if exist
    products =list(WorkData.objects.values_list('product_id',flat=True))
    # test if method post and button save-work
    if request.method=='POST' and 'save-work' in request.POST:
        # get inputs from form
        #    workdata informations
        id = request.POST.get('event-index')
        startTime = request.POST.get('start-time')
        endTime = request.POST.get('end-time')
        fte = request.POST.get('fte')
        extraHours = request.POST.get('extra-hours')
        AbsenteeismRatio = request.POST.get('Absenteeism-ratio')
        UnproductivenessRatio = request.POST.get('Unproductiveness-ratio')
        EfficientyRatio = request.POST.get('Efficienty-ratio')
        startDate = request.POST.get('event-start-date')
        endDate = request.POST.get('event-end-date')
        #cycle informations
        profit_center= Product.objects.all().filter(id = product).values('Profit_center').first()
        smooth_family= request.POST.getlist('smooth_family')
        cycle_time = request.POST.getlist('cycle_time')
        cycle_id = request.POST.getlist('cycle_id')
        # convert starttime and endtime to datetime
        start_time = datetime.strptime(startTime, '%H:%M:%S')
        end_time = datetime.strptime(endTime, '%H:%M:%S')
        if start_time == end_time :
            work_hours= 24
        elif end_time > start_time:
            work_hours= ((end_time - start_time).total_seconds() / 3600)
        else:
            work_hours = ((end_time+ timedelta(days =1)) - start_time ).total_seconds() / 3600
            
        

        # If id exist Update Object if not create new one
        if id and cycle_id:
            # get object workdata
            #first : to get object not queryset 
            work_day=WorkData.objects.all().filter(id=id).first()  #intilisation object
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                #update attributes values with new values
                #update cycle
                work_day.FTEhourByDay=fte
                work_day.date= startDate
                work_day.ExtraHour=extraHours
                work_day.Absenteeism_ratio=AbsenteeismRatio
                work_day.Unproductiveness_ratio=UnproductivenessRatio
                work_day.Efficienty_ratio=EfficientyRatio
                work_day.startTime=startTime
                work_day.endTime=endTime
                work_day.save()
                # update cycle
                # convert two list in dict
                cycle_dict = dict(zip(cycle_id, cycle_time))
                for key,value in cycle_dict.items(): 

                    # get cycle object with key
                    cycle_info= Cycle.objects.all().filter(id=key).first()  #intilisation object
                    cycle_type_input = request.POST.get('cycle-type-'+cycle_info.smooth_family)
                    if cycle_type_input == 'Days':
                        # update cycle_time
                        # cycle_info.cycle_time=float(value) * 16
                        print(end_time)
                        print(type(end_time))
                        cycle_info.cycle_time= float(value) * work_hours
                    if cycle_type_input =='Hours':
                        cycle_info.cycle_time= float(value)
                    cycle_info.save()
                        
                return redirect("../calendar")
        # create new object         
        else :
            # add one day in database
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                # check if day and product_id exists in DB delete and save new data
                if (startDate.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days] ) and (int(product) in products):
                   # delete exist data and save new data 
                   # delete work data with date and product_id 
                    exist_day =WorkData.undeleted_objects.all().filter(date = startDate,product_id = product,owner = 'officiel') 
                    exist_day.delete()
                    # delete cycle with date and profit center
                    exist_cycle=Cycle.undeleted_objects.all().filter(work_day = startDate,profit_center = profit_center.get('Profit_center'),owner = 'officiel')
                    exist_cycle.delete()
                    #Save into Workdata table
                    data = WorkData(date=startDate,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product)
                    data.save()
                    #Save into Cycle table
                    for i,j in zip(smooth_family,cycle_time):
                        cycle_type_input = request.POST.get('cycle-type-'+i)
                        if cycle_type_input == 'Days':
                            # new_cycle_time= float(j) * (endTime - startTime)
                            cycle_info.cycle_time=float(value) * work_hours
                        if cycle_type_input == 'Hours':
                            new_cycle_time=j
                        cycle_data=Cycle(work_day=startDate,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,product_id = product)
                        cycle_data.save()
                    
                    return redirect("../calendar")
                else:
                    ##replace holidays with work data
                    exist_off_days = HolidaysCalendar.undeleted_objects.all().filter(holidaysDate= startDate,product_id = product) 
                    exist_off_days.delete()
                    #Save into Workdata table
                    data = WorkData(date=startDate,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product)
                    data.save()
                    for i,j in zip(smooth_family,cycle_time):
                        cycle_type_input = request.POST.get('cycle-type-'+i)
                        if cycle_type_input == 'Days':
                            new_cycle_time= float(j) * work_hours
                        if cycle_type_input == 'Hours':
                            new_cycle_time=j
                        cycle_data=Cycle(work_day=startDate,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,product_id = product)
                        cycle_data.save()    
                    return redirect("../calendar")
            # add list of days in database       
            else: 
                startDate=datetime.strptime(startDate,'%m/%d/%Y')
                endDate=datetime.strptime(endDate,'%m/%d/%Y')
                delta= endDate-startDate
                day=""
                for i in range(delta.days+1):
                    day= startDate + timedelta(days=i)
                    # check if day and product_id exists delete old object and save new workday and cycle object
                    if (day.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days]) and (int(product) in products):
                        # delete exist workdata and save new workdata
                        exist_days = WorkData.undeleted_objects.all().filter(date = day,product_id = product,owner = 'officiel' ) 
                        exist_days.delete()
                        # delete exist cycle and save new cycle object
                        exist_cycle=Cycle.undeleted_objects.all().filter(work_day = day,profit_center = profit_center.get('Profit_center'),owner = 'officiel')
                        exist_cycle.delete()
                        # Save into workdata table
                        data = WorkData(date=day,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product)
                        data.save()
                        #Save into Cycle table
                        for i,j in zip(smooth_family,cycle_time):
                            cycle_type_input = request.POST.get('cycle-type-'+i)
                            if cycle_type_input == 'Days':
                                new_cycle_time= float(j) * work_hours
                            if cycle_type_input == 'Hours':
                                new_cycle_time=j
                            cycle_data=Cycle(work_day=day,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,product_id = product)
                            cycle_data.save()    
                    else :
                        #replace holidays with work data
                        #get holidays 
                        exist_off_days = HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = day, product_id = product, owner = 'officiel' ) 
                        #delete exist_off_days
                        exist_off_days.delete()
                        #save into workdata data
                        data = WorkData(date=day,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product)
                        data.save()
                        #Save into Cycle table
                        for i,j in zip(smooth_family,cycle_time):
                            cycle_type_input = request.POST.get('cycle-type-'+i)
                            if cycle_type_input == 'Days':
                                print('*****j',j)
                                new_cycle_time= float(j) * work_hours
                            if cycle_type_input == 'Hours':
                                new_cycle_time=j
                            cycle_data=Cycle(work_day=day,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,product_id = product)
                            cycle_data.save()  
                return redirect("../calendar")       
              
#********************custom work data****************************

#create work data for custom calendar
def custom_work(request,division,product):
    # get all work data objects to display in Calendar
    work = WorkData.undeleted_objects.all().filter(product_id = product ,owner = 'marwa') 
    # get list of days from dataBase to compare if exist 
    days = list(work.values_list('date',flat=True))
    # get list of product_id from database to compare if exist
    products =list(WorkData.objects.values_list('product_id',flat=True))       
    if request.method=='POST' and 'save' in request.POST:
        # get inputs values
        # workdata informations
        id = request.POST.get('event-index')
        owner = request.POST.get('owner')
        startTime = request.POST.get('start-time')
        endTime = request.POST.get('end-time')
        fte = request.POST.get('fte')
        extraHours = request.POST.get('extra-hours')
        AbsenteeismRatio = request.POST.get('Absenteeism-ratio')
        UnproductivenessRatio = request.POST.get('Unproductiveness-ratio')
        EfficientyRatio = request.POST.get('Efficienty-ratio')
        startDate = request.POST.get('event-start-date')
        endDate = request.POST.get('event-end-date')
        #cycle informations
        profit_center= Product.objects.all().filter(id = product).values('Profit_center').first()
        smooth_family= request.POST.getlist('smooth_family')
        cycle_time = request.POST.getlist('cycle_time')
        cycle_id = request.POST.getlist('cycle_id')

        start_time = datetime.strptime(startTime, '%H:%M:%S')
        end_time = datetime.strptime(endTime, '%H:%M:%S')
        if start_time == end_time :
            work_hours= 24
        elif end_time > start_time:
            work_hours= ((end_time - start_time).total_seconds() / 3600)
        else:
            work_hours = ((end_time+ timedelta(days =1)) - start_time ).total_seconds() / 3600

        # if id update else save
        if id:
            #get object work data
            #first : to get object not queryset 
            work_day=WorkData.objects.all().filter(id=id).first()  #intilisation object
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                #update attributes values with new values
                work_day.FTEhourByDay=fte
                work_day.date= startDate
                work_day.ExtraHour=extraHours
                work_day.Absenteeism_ratio=AbsenteeismRatio
                work_day.Unproductiveness_ratio=UnproductivenessRatio
                work_day.Efficienty_ratio=EfficientyRatio
                work_day.cycle_time=cycle_time
                work_day.startTime=startTime
                work_day.endTime=endTime
                work_day.save()
                # update cycle
                # convert two list in dict
                cycle_dict = dict(zip(cycle_id, cycle_time))
                for key,value in cycle_dict.items(): 
                    # get cycle object with key
                    cycle_info= Cycle.objects.all().filter(id=key).first()  #intilisation object
                    cycle_type_input = request.POST.get('cycle-type-'+cycle_info.smooth_family)
                    if cycle_type_input == 'Days':
                        # update cycle_time
                        cycle_info.cycle_time=float(value) * 24
                    if cycle_type_input =='Hours':
                        cycle_info.cycle_time= float(value)
                    cycle_info.save()
                return redirect("../customcalendar")
        # create new object         
        else : 
            # add one day in database
            if startDate == endDate:
                startDate= datetime.strptime(startDate,'%m/%d/%Y')
                endDate= datetime.strptime(endDate,'%m/%d/%Y')
                    # check if day and product_id exists in DB don't save else save
                if (startDate.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days] ) and (int(product) in products):
                    # delete workdata with date and product_id and owner
                    exist_day =WorkData.undeleted_objects.all().filter(date = startDate, product_id = product, owner = 'marwa') 
                    exist_day.delete()
                    # delete cycle with date and profit center
                    exist_cycle=Cycle.undeleted_objects.all().filter(work_day = startDate,profit_center = profit_center.get('Profit_center'),owner = 'marwa')
                    exist_cycle.delete()
                    # Save into workdata table
                    data = WorkData(date=startDate,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product,owner = owner)
                    data.save()
                    #Save into Cycle table
                    for i,j in zip(smooth_family,cycle_time):
                        cycle_type_input = request.POST.get('cycle-type-'+i)
                        if cycle_type_input == 'Days':
                            new_cycle_time= float(j) * work_hours
                        if cycle_type_input == 'Hours':
                            new_cycle_time=j
                        cycle_data=Cycle(work_day=startDate,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,owner = owner,product_id = product)
                        cycle_data.save()
                    
                    return redirect("../customcalendar")
                else:
                    #replace holiday with workdata
                    exist_off_days = HolidaysCalendar.undeleted_objects.all().filter(holidaysDate= startDate,product_id = product, owner = 'marwa') 
                    #delete holidays
                    exist_off_days.delete()
                    #save data work object
                    data = WorkData(date=startDate,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product,owner = owner)
                    data.save()
                    #Save into Cycle table
                    for i,j in zip(smooth_family,cycle_time):
                        cycle_type_input = request.POST.get('cycle-type-'+i)
                        if cycle_type_input == 'Days':
                            new_cycle_time= float(j) * work_hours
                        if cycle_type_input == 'Hours':
                            new_cycle_time=j
                        cycle_data=Cycle(work_day=startDate,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,owner = owner,product_id = product)
                        cycle_data.save() 
                    return redirect("../customcalendar")
            # add list of days in database       
            else: 
                startDate=datetime.strptime(startDate,'%m/%d/%Y')
                endDate=datetime.strptime(endDate,'%m/%d/%Y')
                delta= endDate-startDate
                day=""
                for i in range(delta.days+1):
                    day= startDate + timedelta(days=i)
                    # check if day and product_id exists in DB delete old objects of workdata and cycle and save new objects
                    if (day.strftime('%Y-%m-%d') in [day.strftime('%Y-%m-%d') for day in days]) and (int(product) in products):
                        # delete workdata object
                        exist_days = WorkData.undeleted_objects.all().filter(date = day,product_id = product,owner = 'marwa') 
                        exist_days.delete()
                        # delete cycle with date and profit center
                        exist_cycle=Cycle.undeleted_objects.all().filter(work_day = day,profit_center = profit_center.get('Profit_center'),owner = 'marwa')
                        exist_cycle.delete()
                        # save into workdata table
                        data = WorkData(date=day,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product,owner = owner)
                        data.save()
                        # save into cycle object 
                        for i,j in zip(smooth_family,cycle_time):
                            cycle_type_input = request.POST.get('cycle-type-'+i)
                        if cycle_type_input == 'Days':
                            new_cycle_time= float(j) * work_hours
                        if cycle_type_input == 'Hours':
                            new_cycle_time=j  
                            cycle_data=Cycle(work_day=day,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,owner = owner,product_id = product)
                            cycle_data.save() 
                    else :
                        #replace holidays with work data
                        #get holidays 
                        exist_off_days = HolidaysCalendar.undeleted_objects.all().filter(holidaysDate = day,product_id = product,owner = 'marwa') 
                        #delete exist_off_days
                        exist_off_days.delete()
                        #save work data
                        data = WorkData(date=day,startTime=startTime,endTime=endTime,FTEhourByDay=fte,ExtraHour=extraHours,Absenteeism_ratio=AbsenteeismRatio,Unproductiveness_ratio=UnproductivenessRatio, Efficienty_ratio=EfficientyRatio,product_id =product,owner = owner)
                        data.save()
                        # save into cycle object 
                        for i,j in zip(smooth_family,cycle_time):
                            cycle_type_input = request.POST.get('cycle-type-'+i)
                            if cycle_type_input == 'Days':
                                new_cycle_time= float(j) * work_hours
                            if cycle_type_input == 'Hours':
                                new_cycle_time=j
                            cycle_data=Cycle(work_day=day,division=division,profit_center=profit_center.get('Profit_center'),smooth_family=i,cycle_time=new_cycle_time,workdata_id=data.id,owner = owner,product_id = product)
                            cycle_data.save() 
                return redirect("../customcalendar")
    return render(request,"app/calendar/custom_calendar.html",{'product':product,'division':division, 'work':work}) 

#***********CRUD CalendarConfigurationTraitement*****************

# add new object(CalendarConfigurationTraitement)
def create_conf_trait(request,division,product):
    form = CalendarConfigurationTreatementForm(request.POST)
    if request.method == "POST":
     if form.is_valid():
        instance=form.save(commit=False)
        instance.product_id = product
        instance.save()
        messages.success(request,"CalendarConfigurationTraitement created successfully!")
     else:
         messages.error(request,"Form not valid! try again")
    return redirect(f'../{product}/configTrait')
    

#update object(CalendarConfigurationTraitement) by id
def update_conf_trait(request,division):
    #get id
    id = id = request.POST.get('id')
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationTreatement, id = id)
    # pass the object as instance in form
    form = CalendarConfigurationTreatementForm(request.POST or None, instance = obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request,"CalendarConfigurationTraitement updated successfully!")   
        else:
          messages.error(request,"try again !")           
    return redirect(f'./{str(obj.product_id)}/configTrait')
    

# delete object (CalendarConfigurationTraitement) by id
def delete_conf_trait(request, division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationTreatement, id = id)
    # delete object
    obj.soft_delete()
    messages.success(request,"CalendarConfigurationTraitement deleted successfully!")   
    return redirect(f'../{str(obj.product_id)}/configTrait')
    

# restore object (CalendarConfigurationTraitement) by id
def restore_conf_trait(request, division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationTreatement, id = id)
    # restore object
    obj.restore()
    messages.success(request,"CalendarConfigurationTraitement restored successfully!")   
    return redirect(f'../{str(obj.product_id)}/configTrait')
    

# find all CalendarConfigurationTraitement for product 
def config_trait(request, division,product):
    #get CalendarConfigurationTraitementForm
    form = CalendarConfigurationTreatementForm()
    # undeleted_objects object of soft delete manager
    data = CalendarConfigurationTreatement.objects.filter(product__pk = product ).order_by('id')    
    return render(request, "app/CalendarConfigurationTraitement/home_conf_traitement.html", {'data':data,'division':division,'product':product,'form':form})


#***************CRUD CalendarConfigurationCpOrdo*****************

# add new object(CalendarConfigurationCpordo)
def create_conf_cpordo(request,division,product):
    form = CalendarConfigurationCpordoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            instance=form.save(commit=False)
            instance.product_id = product
            instance.save()
            messages.success(request,"CalendarConfigurationCpordo created successfully!")
        else:
            messages.error(request,"Form not valid! try again")     
    return redirect(f'../{product}/configCpordo')
    

#update object(CalendarConfigurationCpordo) by id
def update_conf_cpordo(request, division):
    #get id
    id = id = request.POST.get('id')
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationCpordo, id = id)
    # pass the object as instance in form
    form = CalendarConfigurationCpordoForm(request.POST or None, instance = obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request,"CalendarConfigurationCpordo updated successfully!")
        else:
            messages.error(request,"try again!")    
    return redirect(f'./{str(obj.product_id)}/configCpordo')
    

# delete object (CalendarConfigurationCpordo) by id
def delete_conf_cpordo(request,division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationCpordo, id = id)
    # delete object
    obj.soft_delete()
    messages.success(request,"CalendarConfigurationCpordo deleted successfully!")
    return redirect(f'../{str(obj.product_id)}/configCpordo')


# restore object (CalendarConfigurationCpordo) by id
def restore_conf_cpordo(request,division ,id):
    # fetch the object related to passed id
    obj = get_object_or_404(CalendarConfigurationCpordo, id = id)
    # restore object
    obj.restore()
    messages.success(request,"CalendarConfigurationCpordo restored successfully!")
    return redirect(f'../{str(obj.product_id)}/configCpordo')
    

# find all CalendarConfigurationCpordo for product 
def config_cpordo(request,division ,product):
    #get CalendarConfigurationCpordoForm
    form = CalendarConfigurationCpordoForm()
    # undeleted_objects object of soft delete manager
    data = CalendarConfigurationCpordo.objects.filter(product__pk = product ).order_by('id')    
    return render(request, "app/CalendarConfigurationCpordo/home_conf_cpordo.html", {'data':data,'division':division,'product':product,'form':form})

#********************** Home*****************************

def home_page(request):
    
    return render(request,'app/home/index.html')

#*******************copy calendar*************************
def copy_calendar(request,division,product):
    #Delete holidays
    holidays_data = HolidaysCalendar.objects.all().filter(product_id = product,owner = 'officiel')
    holidays_data.delete()
    #Delete work
    work_data = WorkData.objects.all().filter(product_id = product,owner = 'officiel')
    work_data.delete() 
    # Delete cycle
    cycle_data = Cycle.objects.all().filter(product_id = product,owner = 'officiel')
    cycle_data.delete() 
    #get product copied id 
    product_copied= request.POST.get('product_copied')
    #get holiday object with product id
    holidays_data = HolidaysCalendar.undeleted_objects.all().filter(product_id = product_copied, owner = 'officiel')
    #save holiday object in DB
    for data in holidays_data:
        holidays = HolidaysCalendar(name=data.name,holidaysDate=data.holidaysDate,product_id = product)
        holidays.save()

    #get work data object with product id 
    work = WorkData.undeleted_objects.all().filter(product_id = product_copied ,owner = 'officiel')  
    #save data for loop work
    for data in work:
        work_data = WorkData(date=data.date,startTime=data.startTime,endTime=data.endTime,FTEhourByDay=data.FTEhourByDay,ExtraHour=data.ExtraHour,Absenteeism_ratio=data.Absenteeism_ratio,Unproductiveness_ratio=data.Unproductiveness_ratio,Efficienty_ratio=data.Efficienty_ratio,product_id = product)
        work_data.save()
        # get profit center from product
        # profit_center =Product.undeleted_objects.filter(id=product).values('Profit_center')
        # get cycle object with product_id and workdata_id 
        # cycles = Cycle.undeleted_objects.all().filter(product_id = product_copied, workdata_id=data.id, owner = 'officiel') 
        # save cycle with new value of workdata_id 
        # for cycle in cycles:
        #     custom_cycle= Cycle(work_day=cycle.work_day,division=cycle.division,profit_center=profit_center,smooth_family=cycle.smooth_family,cycle_time=cycle.cycle_time, workdata_id=work_data.id,product_id = product)
        #     custom_cycle.save()  
    return redirect("../calendar")

#*********************Save uploads************************
#upload files
def upload_files(request):  

    return render(request,'app/files/file.html')  

#save coois   
def save_coois(request):
    conn = psycopg2.connect(host='localhost',dbname='mps_database',user='postgres',password='admin',port='5432')
    try:
        #Delete coois data 
        coois_data = Coois.undeleted_objects.all().filter(created_by='Marwa')
        coois_data.delete()
        #Save file to DB
        if request.method == 'POST' and request.FILES['coois']:
            file=request.FILES['coois']
            import_coois(file,conn)
            messages.success(request,"COOIS file uploaded successfully!") 
    except Exception:
        messages.error(request,"unable to upload files,not exist or unreadable") 
        print('unable to upload files,not exist or unreadable')
    return redirect("./upload")    
        
#save zpp   
def save_zpp(request):
    conn = psycopg2.connect(host='localhost',dbname='mps_database',user='postgres',password='admin',port='5432')
    #Delete zpp data 
    zpp_data = Zpp.undeleted_objects.all().filter(created_by='Marwa')
    zpp_data.delete()
    
    #Save file to DB
    try:
        if request.method == 'POST' and request.FILES['zpp']:
            file=request.FILES['zpp']
            import_zpp(file,conn)
            messages.success(request,"ZPP file uploaded successfully!") 
         
    except Exception:
        messages.error(request,"unable to upload ZPP files,not exist or unreadable") 
        print('unable to upload files,not exist or unreadable')
    return redirect("./upload")     
    
    
#********************************Upload COOIS************************************

def import_coois(file,conn):
    #read file with pandas
    dc=pd.read_excel(file)
    #insert informations into file
    dc.insert(0,'created_at',datetime.now())
    dc.insert(1,'updated_at',datetime.now())
    dc.insert(2,'created_by','Marwa')
    dc.insert(3,'updated_by','Marwa')
    dc.insert(4,'is_deleted',False)
    dc.insert(5,'deleted_by','Marwa')
    dc.insert(6,'deleted_at',datetime.now())
    dc.insert(7,'restored_at',datetime.now())
    dc.insert(8,'restored_by','Marwa')
    
    # Using the StringIO method to set
    # as file object
    print(dc.head(10))
    coois = StringIO()
    #convert file to csv
    coois.write(dc.to_csv(index=None , header=None))
    # This will make the cursor at index 0
    coois.seek(0)
    with conn.cursor() as c:
        c.copy_from(
            file=coois,
            #file name in DB
            table="app_coois",
            columns=[
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
                'is_deleted',
                'deleted_by',
                'deleted_at',
                'restored_at',
                'restored_by',
                'division',
                'profit_centre',
                'order',
                'material',
                'designation',
                'order_type',
                'order_quantity',
                'date_start_plan',
                'date_end_plan',
                'fixation',
                'manager',
                'order_stat',
                'customer_order',
                'date_end_real',
                'entered_by',
                
            ],

            null="",
            sep=",",

        )
    conn.commit()

#********************************Upload ZPP_MD_STOCK*****************************

def import_zpp(file,conn):
    #read file with pandas
    dc=pd.read_excel(file,names=['material','plan_date','element','data_element_planif','message','needs','qte_available','date_reordo','supplier','customer'])
    #insert informations into file
    dc.insert(0,'created_at',datetime.now())
    dc.insert(1,'updated_at',datetime.now())
    dc.insert(2,'created_by','Marwa')
    dc.insert(3,'updated_by','Marwa')
    dc.insert(4,'is_deleted',False)
    dc.insert(5,'deleted_by','Marwa')
    dc.insert(6,'deleted_at',datetime.now())
    dc.insert(7,'restored_at',datetime.now())
    dc.insert(8,'restored_by','Marwa')
    # delete the slash and the part after the slash
    dc['data_element_planif']= dc['data_element_planif'].str.split("/").str[0]
    # delete the zeros on the left
    dc['data_element_planif']= dc['data_element_planif'].str.lstrip("0")
    
    

    # Using the StringIO method to set
    # as file object
    zpp = StringIO()
    #convert file to csv
    zpp.write(dc.to_csv(index=None , header=None,sep=';'))
    # This will make the cursor at index 0
    zpp.seek(0)
    with conn.cursor() as c:
        c.copy_from(
            file=zpp,
            #file name in DB
            table="app_zpp",
            columns=[
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
                'is_deleted',
                'deleted_by',
                'deleted_at',
                'restored_at',
                'restored_by',
                'material',
                'plan_date',
                'element',
                'data_element_planif',
                'message',
                'needs',
                'qte_available',
                'date_reordo',
                'supplier',
                'customer', 
                    
            ],

            null="",
            sep=";",
            

        )
    conn.commit()

#*************************Shopfloor and smoothing**********************

# @allowed_users(allowed_roles=["Planificateur"])
# merge between coois and zpp and material
def shopfloor(request):
    
    # Get Data from DB
    # to use in shopfloor
    zpp_data=Zpp.objects.filter(created_by= 'Marwa').values('material','data_element_planif','created_by','message','date_reordo')
    coois_data= Coois.objects.all().filter(created_by= 'Marwa').values()
    material_data=Material.undeleted_objects.values('material','product__program','product__division__name','created_by','workstation','AllocatedTime','Leadtime','Allocated_Time_On_Workstation','Smooth_Family')

    #Convert to DataFrame
    df_zpp=pd.DataFrame(list(zpp_data))
    df_coois=pd.DataFrame(list(coois_data))
    df_material=pd.DataFrame(list(material_data))
    # rename df_material column 
    df_material=df_material.rename(columns={'product__program':'program','product__division__name':'division'})


    #add column key for zpp (concatinate  material and data_element_planif and created_by  )
    df_zpp['key']=df_zpp['material'].astype(str)+df_zpp['data_element_planif'].astype(str)+df_zpp['created_by'].astype(str)
    #add column key for coois (concatinate material, order, created_by )    
    df_coois['key']=df_coois['material'].astype(str)+df_coois['order'].astype(str)+df_coois['created_by'].astype(str)

    #add column key for material (concatinate material, created_by )  
    df_material['key']=df_material['material'].astype(str)+df_material['division'].astype(str)+df_material['created_by'].astype(str)
    #add column key for coois (concatinate material,division,profit_centre, created_by )    
    df_coois['key2']=df_coois['material'].astype(str)+df_coois['division'].astype(str)+df_coois['created_by'].astype(str)


    #Convert df_zpp to dict
    df_zpp_dict_message=dict(zip(df_zpp.key, df_zpp.message))
    df_zpp_dict_date_reordo=dict(zip(df_zpp.key, df_zpp.date_reordo))

    #Merge ZPP and COOIS with keys
    df_coois['message']=df_coois['key'].map(df_zpp_dict_message)
    df_coois['date_reordo']=df_coois['key'].map(df_zpp_dict_date_reordo)

    #convert df_material to dict
    df_material_dict_AllocatedTime= dict((zip(df_material.key,df_material.AllocatedTime)))
    df_material_dict_Leadtime= dict((zip(df_material.key,df_material.Leadtime)))
    df_material_dict_workstation= dict((zip(df_material.key,df_material.workstation)))
    df_material_dict_Allocated_Time_On_Workstation= dict((zip(df_material.key,df_material.Allocated_Time_On_Workstation)))
    df_material_dict_Smooth_Family= dict((zip(df_material.key,df_material.Smooth_Family)))


    #Merge coois and material with keys
    df_coois['AllocatedTime']=df_coois['key2'].map(df_material_dict_AllocatedTime)
    df_coois['Leadtime']=df_coois['key2'].map(df_material_dict_Leadtime)
    df_coois['workstation']=df_coois['key2'].map(df_material_dict_workstation)
    df_coois['Allocated_Time_On_Workstation']=df_coois['key2'].map(df_material_dict_Allocated_Time_On_Workstation)
    df_coois['Smooth_Family']=df_coois['key2'].map(df_material_dict_Smooth_Family)

    # add conditions :
    # 1: for Ranking : equal date reordo if exist else equal date end plan
    df_coois['Ranking']=np.where((df_coois['date_reordo'].isna()),(pd.to_datetime(df_coois['date_end_plan'])),(pd.to_datetime(df_coois['date_reordo'])))
    # 2: for closed  : equal true where order_stat containes TCLO ou LIVR
    df_coois['closed']=np.where(df_coois['order_stat'].str.contains('TCLO|LIVR'),True,False)
    records=df_coois.sort_values(['Smooth_Family','Ranking'])
    return render(request,'app/Shopfloor/Shopfloor.html',{'records': records} ) 

#create shopfloor
# get inputs value, calculate smoothing end date and save 
def create_shopfloor(request):
    
    if request.method=='POST':
        id = request.POST.getlist('index')
        # get inputs values
        division = request.POST.getlist('division')
        profit_centre = request.POST.getlist('profit_centre')
        order = request.POST.getlist('order')
        material = request.POST.getlist('material')
        designation = request.POST.getlist('designation')
        order_type = request.POST.getlist('order_type')
        order_quantity = request.POST.getlist('order_quantity')
        date_start_plan= request.POST.getlist('date_start_plan')
        date_end_plan = request.POST.getlist('date_end_plan')
        fixation = request.POST.getlist('fixation')
        date_reordo = request.POST.getlist('date_reordo')
        message = request.POST.getlist('message')
        order_stat = request.POST.getlist('order_stat')
        customer_order = request.POST.getlist('customer_order')
        date_end_real = request.POST.getlist('date_end_real')
        AllocatedTime = request.POST.getlist('AllocatedTime')
        Leadtime = request.POST.getlist('Leadtime')
        workstation = request.POST.getlist('workstation')
        Allocated_Time_On_Workstation = request.POST.getlist('Allocated_Time_On_Workstation')
        Smooth_Family = request.POST.getlist('Smooth_Family')
        Ranking = request.POST.getlist('Ranking')
        Freeze_end_date = request.POST.getlist('freeze_end_date')
        Remain_to_do = request.POST.getlist('Remain to do')
        closed = request.POST.getlist('closed')
        calendar_type=request.POST.get('calendar')

        # make holidays and cycle_data as global varibale to reduce access to database
        global holidays, cycle_data
        if calendar_type == 'official':
            holidays = HolidaysCalendar.undeleted_objects.values_list('holidaysDate',flat=True).filter( owner = 'officiel') 
            cycle_data=Cycle.undeleted_objects.values('product__division__name','profit_center','smooth_family','cycle_time','work_day').filter( owner = 'officiel') 
            # print('cycle_data', cycle_data)
        else:
            holidays = HolidaysCalendar.undeleted_objects.values_list('holidaysDate',flat=True).filter( owner = 'marwa') 
            cycle_data=Cycle.undeleted_objects.values('product__division__name','profit_center','smooth_family','cycle_time','work_day').filter( owner = 'marwa') 
        #Convert Input Data to DateFrame
        data={
            'division':division,
            'profit_centre':profit_centre,
            'order':order,
            'material':material,
            'designation':designation,
            'order_type':order_type,
            'order_quantity':order_quantity,
            'date_start_plan':date_start_plan,
            'date_end_plan': date_end_plan,
            'fixation':fixation,
            'date_reordo':date_reordo,
            'message':message,
            'order_stat':order_stat,
            'customer_order':customer_order,
            'date_end_real':date_end_real, 
            'AllocatedTime':AllocatedTime, 
            'Leadtime':Leadtime, 
            'workstation':workstation,
            'Allocated_Time_On_Workstation':Allocated_Time_On_Workstation, 
            'Smooth_Family':Smooth_Family,
            'Ranking':Ranking, 
            'Freeze_end_date':Freeze_end_date, 
            'Remain_to_do':Remain_to_do, 
            'closed':closed,
            }
        # convert data to dataframe 
        df=pd.DataFrame.from_dict(data)
        # convert freeze_end_date to datetime 
        df['Freeze_end_date'] = pd.to_datetime(df['Freeze_end_date'])
        # delete old objects of shopfloor and save new objects
        # Shopfloor.objects.all().delete()
        # df.to_csv('df_before_calcul.csv')
        # print(df)
             

        # #Check if at least the first end date is present for each Smooth Family
        # df_for_check = df[df['closed'].str.contains('False')].groupby(["Smooth_Family"], as_index=False)["Freeze_end_date"].first()
        # print(data)
        df_for_check = df[df['closed'].str.contains('False')].groupby(["Smooth_Family"], as_index=False)["Freeze_end_date"].first()        
        # print('#'*50)
        # print(df_for_check)
        # test line by line to return the index of smooth family is not filled
        for i in range(len(df_for_check)):
            if (pd.isnull(df_for_check.loc[i,'Freeze_end_date'])):
                messages.error(request,'Please fill at least the first Freeze end date, for the Smooth Family: '+df_for_check.loc[i,'Smooth_Family'])
                return redirect("shopfloor")
                # return render(request, 'app/Shopfloor/result.html')
        #call function smoothing_calculate to calcul smoothing end date 
        df=smoothing_calculate(df)
        # delete key,freezed, key_start_day column
        del df['key']
        del df['freezed']
        del df['key_start_day']
        # delete index from df
        df=df.reset_index(drop=True)
        # save shofloor with version 
        # get version_data 
        version_number = Shopfloor.objects.values('version').order_by('-version').first()
        # test if data is empty
        if not version_number :
            print('Emptyyy')
            df['version'] = 1
        else:
            df['version'] = version_number['version']+1
        df['shared']= 'False'
        # df.to_csv('df_after_save.csv')
        save_shopfloor(df)
        messages.success(request,"Data saved successfully!") 
        return redirect(filter)
        
# @allowed_users(allowed_roles=["Planificateur"]) 
#  calculate smoothing end date to use in create shopfloor       
def smoothing_calculate(df_data):
    #Get Work date data
    # cycle_data=Cycle.undeleted_objects.values('profit_center','smooth_family','cycle_time','work_day') 
    #Convert to DataFrame cycle_data( globale variable)
    df_cycle_data=pd.DataFrame(list(cycle_data))
    # concatinate profit_center and smooth_family and work_day
    df_cycle_data['key']= df_cycle_data['product__division__name'].astype(str)+df_cycle_data['profit_center'].astype(str)+df_cycle_data['smooth_family'].astype(str)+df_cycle_data['work_day'].astype(str)
   # df_product_work_data_dict_date=dict(zip(df_product_work_data.key, df_product_work_data.workdate))
    df_dict_cycle=dict(zip(df_cycle_data.key, df_cycle_data.cycle_time))
    #Get Shopfloor from DB
    # data=Shopfloor.objects.all().values()
    # df_data=pd.DataFrame(list(data))
    # sort values with Ranking
    df_data=df_data.sort_values('Ranking') 
    #Add col freezed to know how row is freezed
    df_data['freezed']=np.where((df_data['Freeze_end_date'].notna()),'Freezed','not_freezed')
    df_data['key']=df_data['division'].astype(str)+df_data['profit_centre'].astype(str)+df_data['Smooth_Family'].astype(str)+pd.to_datetime(df_data['Freeze_end_date']).astype(str)
    df_data[['Freeze_end_date']] = df_data[['Freeze_end_date']].astype(object).where(df_data[['Freeze_end_date']].notnull(), None)
    df_data['smoothing_end_date']=df_data['Freeze_end_date']
    # df_data.to_csv('freeze.csv')
    df_data.insert(0,'key_start_day','')
    # *********************
    df_closed_false= df_data[df_data['closed']=='False']
    # df_closed_false=df_closed_false.reset_index()
    # del df_closed_false['index']
    print(df_closed_false)

    df_closed_false = df_closed_false.sort_values(['Smooth_Family','Ranking']).reset_index()
    del df_closed_false['index']
    print(df_closed_false)
    df_closed_false.to_csv('df_closed_false.csv')
    df_closed_true = df_data[df_data['closed'] =='True']
    df_closed_true=df_closed_true.reset_index()
    del df_closed_true['index']
    # df_closed_true.to_csv('df_closed_true.csv') 
    # *********************
    for i in range(len(df_closed_false)-1):
        # test if not freezed and not closed calcul smoothing
        # if (df_data.loc[i+1,'freezed']=='not_freezed') and (df_data.loc[i+1,'closed']=='False'):

        if (df_closed_false.loc[i+1,'freezed']=='not_freezed'):
            df_closed_false.loc[i+1,'smoothing_end_date'] = smooth_date_calcul(df_closed_false.loc[i,'smoothing_end_date'],df_dict_cycle.items(),df_closed_false.loc[i,'division'],df_closed_false.loc[i,'profit_centre'],df_closed_false.loc[i,'Smooth_Family'])
    df_closed_false.to_csv('df_after_smoothing.csv')
    df_data = pd.concat([df_closed_true, df_closed_false])
    # df_closed_false.to_csv('df_closed_false.csv')
    # df_data.to_csv('df_concat.csv')
    return df_data
    
    

#calcul smooth end date(Recursive Function) to use in smoothing_calculate
def smooth_date_calcul(current_date,table,division,profit_center,Smooth_Family,prev_cycle=None,prev_date=None):
    
    #Get cycle for current day
    key_date=str(division)+str(profit_center)+str(Smooth_Family)+str(current_date).split(' ')[0]
    
    #initial case treatment (when prev_date =  current_date)
    if prev_date is None:
        prev_date=current_date
    # Check and get cycle
    try:
        # key : contains the concatenation between division and profit_center and smooth family and date of the table 
        # value :cycle time
        for key,value in table:
            if key_date == key:
                cycle=value
        print('cycle: ')
        print(cycle)     
    #when cycle not found  in table return date(1900,1,1)    
    except Exception:
        
        return datetime(1900, 1, 1, 6) 
       
          
    #stop condition to avoid the infinite loop
    if cycle==prev_cycle:
        return current_date
    
    # get start time for current date
    # flat=True this will mean the returned results are single values, rather than one-tuples
    start_time = WorkData.undeleted_objects.filter(date=current_date).values_list('startTime',flat=True).first()
    # get end time for current date
    end_time = WorkData.undeleted_objects.filter(date=current_date).values_list('endTime',flat=True).first()
      
    # dictionary of business_hours
    business_hours = {
    "from": start_time, # startTime
    "to": end_time,  # endTime
    }

    # function is_in_open_hours
    def is_in_open_hours(dt):
            return  dt.date() not in holidays \
            and business_hours["from"].hour <= dt.time().hour < business_hours["to"].hour

    # function get_next_open_datetime 
    def get_next_open_datetime(dt):
        while True:
            dt = dt + timedelta(days=1)
            # check if open date
            if dt.date() not in holidays:
                # combine date and hour
                # dt = datetime.combine(dt.date(), business_hours["from"])
                dt = datetime.combine(dt.date(), business_hours["from"])+timedelta(minutes=dt.time().minute)
                return dt
    
    # function add hours
    def add_hours(dt, hours):
        while hours > 0:
            if is_in_open_hours(dt) :
                dt = dt + timedelta(hours=1)
                hours = hours - 1
            else:
                dt = get_next_open_datetime(dt)

        if hours < 1:
            dt= dt+timedelta(hours=hours)
        # check if dt is the last hour of work
        if  dt.time().hour == business_hours["to"].hour or dt.time().hour > business_hours["to"].hour:
            dt = get_next_open_datetime(dt)
        return dt

    new_date=add_hours(prev_date, cycle)
    return   smooth_date_calcul(new_date,table,division,profit_center,Smooth_Family,cycle,current_date)

  
# save shoploor to use in create_shopfloor
def save_shopfloor(df):
    conn = psycopg2.connect(host='localhost',dbname='mps_database',user='postgres',password='admin',port='5432')
    #insert base informations into file
    df.insert(0,'created_at',datetime.now())
    df.insert(1,'updated_at',datetime.now())
    df.insert(2,'created_by','Marwa')
    df.insert(3,'updated_by','Marwa')
    df.insert(4,'is_deleted',False)
    df.insert(5,'deleted_by','')
    df.insert(6,'deleted_at',datetime.now())
    df.insert(7,'restored_at',datetime.now())
    df.insert(8,'restored_by','')

    # Using the StringIO method to set
    # as file object
    shopfloor = StringIO()

    # df.to_csv('dfSaveShopfloor.csv',index=False)

    #convert file to csv
    shopfloor.write(df.to_csv(index=False , header=None,sep=';'))
    # This will make the cursor at index 0
    shopfloor.seek(0)
    with conn.cursor() as c:
        c.copy_from(
            file=shopfloor,
            #file name in DB
            table="app_shopfloor",
            columns=[
                    'created_at',
                    'updated_at',
                    'created_by',
                    'updated_by',
                    'is_deleted',
                    'deleted_by',
                    'deleted_at',
                    'restored_at',
                    'restored_by',
                    'division',
                    'profit_centre',
                    'order',
                    'material',
                    'designation',
                    'order_type',
                    'order_quantity',
                    'date_start_plan',
                    'date_end_plan',
                    'fixation',
                    'date_reordo',
                    'message',
                    'order_stat',
                    'customer_order',
                    'date_end_real',
                    'AllocatedTime',
                    'Leadtime',
                    'workstation',
                    'Allocated_Time_On_Workstation',
                    'Smooth_Family',
                    'Ranking',
                    'Freeze_end_date',
                    'Remain_to_do',
                    'closed',
                    'smoothing_end_date',
                     'version',
                     'shared',
                    ],

            null="",
            sep=";",
        )
    conn.commit()


# filter by division, profit_center and panning, week to get versions
def filter(request):
    divisions_list= Division.undeleted_objects.values('name').distinct().order_by('name')
    center_profit_list = Product.undeleted_objects.values('Profit_center').distinct().order_by('Profit_center')
    planning_list= Product.undeleted_objects.values('planning').distinct().order_by('planning')
    dates=Shopfloor.objects.values('created_at__year','created_at__week').distinct()

    division= profit_center= planning=versions= date =None

    if request.method == "POST":
        division= request.POST.get('division_name')
        profit_center= request.POST.get('center_profit')
        planning= request.POST.get('planning')
        date= request.POST.get('week')
        

        year=date.split(',')[0]
        week=date.split(',')[1]

        versions = Shopfloor.objects.values('version','shared').filter(division=division,profit_centre= profit_center,designation=planning,created_at__week__gte=week, created_at__year=year).distinct().order_by('version')
        
    return render( request,'app/Shopfloor/filter.html',{'divisions_list':divisions_list,'center_profit_list':center_profit_list,'planning_list':planning_list,
    'versions':versions,
    'division':division,
    'date':date,
    'profit_center':profit_center,
    'planning':planning,
    'dates':dates
    })

# def result diplay result of shoploor data with version  
def result(request):

    division= profit_center= planning=version= None
    if request.method == "POST":
        division= request.POST.get('division')
        profit_center= request.POST.get('profit_center')
        planning= request.POST.get('planning')
        version= request.POST.get('version')
        

    data=Shopfloor.objects.all().order_by('version','smoothing_end_date','closed','Smooth_Family','Ranking').filter(division=division,profit_centre=profit_center,designation=planning,version=version)
    # print(data)
    # if request.method == 'POST':
    #     # Download file 
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename=Smoothing_result.csv'
    #     # data.to_csv(path_or_buf=response,sep=';',float_format='%.2f',index=False,decimal=",")
    #     df_data=pd.DataFrame(list(data))
    #     df_data.to_csv(path_or_buf=response,index=False)
    #     return response
    return render(request,'app/Shopfloor/result.html',{'records':data,'division':division,'profit_center':profit_center,'planning':planning,'version':version}) 

def result_sharing(request):
    division= profit_center= planning=version=data= None
    if request.method == "POST":
        division= request.POST.get('division')
        profit_center= request.POST.get('profit_center')
        planning= request.POST.get('planning')
        version= request.POST.get('version')
        
        data=Shopfloor.objects.all().filter(division=division,profit_centre=profit_center,designation=planning)
        data.update(shared=False)
        data=Shopfloor.objects.all().filter(division=division,profit_centre=profit_center,designation=planning,version=version)
        data.update(shared=True)
    # return redirect("../result")
    return render(request,'app/Shopfloor/result.html',{'records':data,'division':division,'profit_center':profit_center,'planning':planning,'version':version}) 


#******************************Planning********************************   
# filter panning result
def filter_planning(request):
    divisions_list= Division.undeleted_objects.values('name').distinct().order_by('name')
    center_profit_list = Product.undeleted_objects.values('Profit_center').distinct().order_by('Profit_center')
    planning_list= Product.undeleted_objects.values('planning').distinct().order_by('planning')
    smooth_family_list=Material.undeleted_objects.values('Smooth_Family').distinct().order_by('Smooth_Family')
    material_list=Material.undeleted_objects.values('material').distinct().order_by('material')
    

    division= profit_center= planning=df_data=df_cycle=df_work_days=smooth_family_selected=material_selected=from_date=to_date =date_from= date_to=None
    demand_prod_planning.week_count=None
    demand_prod_planning.week_count_axis_x=None
    demand_prod_planning.month_count=None
    demand_prod_planning.month_count_axis_x=None
    cycle_time_kpi.cycle_count=None
    cycle_time_kpi.week_cycle_count_axis_x=None
    cycle_time_kpi.smooth_family=None
    cycle_time_kpi.smooth_family_month=None
    cycle_time_kpi.cycle_count_month=None
    cycle_time_kpi.month_cycle_count_axis_x=None
    production_plan_kpi.date_production_week=None
    production_plan_kpi.date_production_month=None
    demand_prod_planning.work_days_count =None
    demand_prod_planning.work_days_count_month=None



    if request.method == "POST":
        division= request.POST.get('division_name')
        profit_center= request.POST.get('center_profit')
        planning= request.POST.get('planning')
        smooth_family_selected = request.POST.getlist('smooth_family')
        material_selected= request.POST.getlist('material')
        from_date= request.POST.get('from')
        to_date= request.POST.get('to')

        date_from = datetime.strptime(from_date,'%Y-%m-%d')
        date_to = datetime.strptime(to_date,'%Y-%m-%d')

        #Get data
        data=Shopfloor.objects.all().filter(shared=True,division=division,profit_centre= profit_center,designation=planning,Smooth_Family__in=smooth_family_selected,material__in=material_selected)
        division_id=Division.undeleted_objects.all().filter(name=division).values('pk').first()
        cycle_data=Cycle.undeleted_objects.all().filter(division=division_id['pk'],profit_center =profit_center,smooth_family__in=smooth_family_selected,owner='officiel')
        work_days=WorkData.undeleted_objects.values('date').filter(product__division=division_id['pk'],product__Profit_center =profit_center,owner='officiel').distinct()
        print(work_days)
       
        if not data:
            messages.error(request,"No data with selected filter!") 
            return render(request,'app/planning.html',{'divisions_list':divisions_list,'center_profit_list':center_profit_list,'planning_list':planning_list,
            'smooth_family_list':smooth_family_list,
            'material_list':material_list,
            })

        df_data=pd.DataFrame(data.values())
        df_cycle=pd.DataFrame(cycle_data.values())
        df_work_days=pd.DataFrame(work_days.values())

        # date
        df_data['date']=np.where((df_data['date_reordo'].isna()),(df_data['date_end_plan']),(df_data['date_reordo']))
        # call function demand_prod_planning
        demand_prod_planning(df_data,df_work_days,date_from,date_to)
        # call function demand_prod_planning
        production_plan_kpi(df_data)
        if cycle_data:
            # call function cycle_time_kpi 
            cycle_time_kpi(df_cycle,date_from,date_to)
        

    return render(request,'app/planning.html',{'divisions_list':divisions_list,'center_profit_list':center_profit_list,'planning_list':planning_list,'smooth_family_list':smooth_family_list,'material_list':material_list,
    'division':division,
    'profit_center':profit_center,
    'planning':planning,
    'records':df_data,
    'df_cycle':df_cycle,
    'df_work_days':df_work_days,
    'from_date':from_date,
    'to_date':to_date,
    'date_from':date_from,
    'date_to':date_to,
    'smooth_family_selected':smooth_family_selected,
    'material_selected':material_selected,
    'week_count':demand_prod_planning.week_count,
    'week_count_axis_x':demand_prod_planning.week_count_axis_x,
    'month_count':demand_prod_planning.month_count,
    'month_count_axis_x':demand_prod_planning.month_count_axis_x,
    'cycle_count':cycle_time_kpi.cycle_count,
    'week_cycle_count_axis_x':cycle_time_kpi.week_cycle_count_axis_x,
    'smooth_family': cycle_time_kpi.smooth_family,
    'cycle_count_month':cycle_time_kpi.cycle_count_month,
    'month_cycle_count_axis_x':cycle_time_kpi.month_cycle_count_axis_x,
    'smooth_family_month':cycle_time_kpi.smooth_family_month,
    'date_production_week':production_plan_kpi.date_production_week,
    'date_production_month':production_plan_kpi.date_production_month,
    'work_days_count_week': demand_prod_planning.work_days_count,
    'work_days_count_month':demand_prod_planning.work_days_count_month,
    })



# calculate nomber of OF and OP ( wek and month)
def demand_prod_planning(df_data,df_work_days,date_from,date_to):

    # get df between two dates
    df_data_demand_prod_interval=df_data[(df_data['date'] > date_from.date()) & (df_data['date'] <= date_to.date())]
    # week of date
    df_data_demand_prod_interval['date_week']=pd.to_datetime(df_data_demand_prod_interval['date']).dt.week
    # month of date
    df_data_demand_prod_interval['date_month']=pd.to_datetime(df_data_demand_prod_interval['date']).dt.month
    # year of date
    df_data_demand_prod_interval['date_year']=pd.to_datetime(df_data_demand_prod_interval['date']).dt.year
    # concatenate year and week
    df_data_demand_prod_interval['date_year_week']=df_data_demand_prod_interval['date_year'].astype(str)+'-'+'W'+df_data_demand_prod_interval['date_week'].astype(str)
    # concatenate year and month
    df_data_demand_prod_interval['date_year_month']=df_data_demand_prod_interval['date_year'].astype(str)+'-'+'M'+df_data_demand_prod_interval['date_month'].astype(str)
    # new column contains OF or OP
    df_data_demand_prod_interval['order_nature']=np.where((df_data_demand_prod_interval['order_type'].str.startswith('YP')),('OF'),('OP'))
    # new column contains closed and order nature to display closed 
    df_data_demand_prod_interval['order_nature_closed']=df_data_demand_prod_interval['order_nature'].astype('str')+df_data_demand_prod_interval['closed'].astype('str')
    # use unstack and stack to get duplicate data (for chart js)

    week_count=df_data_demand_prod_interval.groupby(['date_year_week','order_nature_closed'])['id'].count().unstack().fillna(0).stack().reset_index()
    # get year from date_year_week 
    week_count['year']=week_count['date_year_week'].str.split('-W').str[0].astype(int)
    # get week from date_year_week 
    week_count['week']=week_count['date_year_week'].str.split('-W').str[1].astype(int)
    # sort values with year week (to get orderd values(year, week))
    week_count=week_count.sort_values(by=['year','week']).reset_index()
    # get unique date_year_week (because value date_year_week duplicate)
    week_count_axis_x=week_count['date_year_week'].unique()
    

    ### month
    month_count=df_data_demand_prod_interval.groupby(['date_year_month','order_nature_closed'])['id'].count().unstack().fillna(0).stack().reset_index()
    month_count['year']=month_count['date_year_month'].str.split('-M').str[0].astype(int)
    month_count['week']=month_count['date_year_month'].str.split('-M').str[1].astype(int)
    month_count=month_count.sort_values(by=['year','week']).reset_index()
    month_count_axis_x=month_count['date_year_month'].unique()
    
    demand_prod_planning.week_count=week_count
    demand_prod_planning.week_count_axis_x=week_count_axis_x
    demand_prod_planning.month_count=month_count
    demand_prod_planning.month_count_axis_x=month_count_axis_x

    

    # calcul Demonstrated capacity (week and month)
    # get previous_month
    previous_month = date_from - relativedelta(months=1)
    df_prev_month = df_data[(df_data['date'] > previous_month.date()) & (df_data['date'] <= date_from.date())]

    #  calcul sum of closed in previous_month
    df_prev_month_closed=df_prev_month[df_prev_month['closed']==True]
    previous_month_closed_count=df_prev_month_closed.shape[0]

    #calcul number of work_days in previous_month
    delta = date_from - previous_month
    days = [previous_month + timedelta(days=i) for i in range(delta.days + 1)]
    df_dates_prev_month=pd.DataFrame(days , columns = ['dates'])
    work_days_in_previous_month = df_dates_prev_month[df_dates_prev_month['dates'].isin(df_work_days['date']) == True]
    work_days_in_previous_month_count = work_days_in_previous_month.count()
    
    # calcul number of work_days in period(week or month)
    df_work_days['date_week']=pd.to_datetime(df_work_days['date']).dt.week
    df_work_days['date_year']=pd.to_datetime(df_work_days['date']).dt.year
    work_days_count=df_work_days.groupby(['date_week','date_year'])['id'].count().reset_index()
    work_days_count['date_year_week']= work_days_count['date_year'].astype(str)+'-'+'W'+work_days_count['date_week'].astype(str)
    work_days_count = work_days_count[work_days_count['date_year_week'].isin(week_count_axis_x)]
    work_days_count['result'] = work_days_count['id'] * (previous_month_closed_count / work_days_in_previous_month_count['dates'])
    

    # calcul number of work_days in period(week or month)
    df_work_days['date_month']=pd.to_datetime(df_work_days['date']).dt.month
    work_days_count_month=df_work_days.groupby(['date_month','date_year'])['id'].count().reset_index()
    work_days_count_month['date_year_month']= work_days_count_month['date_year'].astype(str)+'-'+'M'+work_days_count_month['date_month'].astype(str)
    work_days_count_month = work_days_count_month[work_days_count_month['date_year_month'].isin(month_count_axis_x)]
    work_days_count_month['result'] = work_days_count_month['id'] * (previous_month_closed_count / work_days_in_previous_month_count['dates'])
     


    demand_prod_planning.work_days_count=work_days_count
    demand_prod_planning.work_days_count_month=work_days_count_month

    




# Kpi cycle time per smooth family (week and month)
def cycle_time_kpi(df_data,date_from,date_to):

    df_cycle_time_interval = df_data[(df_data['work_day'] > date_from.date()) & (df_data['work_day'] <= date_to.date())]
    # work_day_week
    df_cycle_time_interval['work_day_week']=pd.to_datetime(df_cycle_time_interval['work_day']).dt.week
    # work_day_month
    df_cycle_time_interval['work_day_month']=pd.to_datetime(df_cycle_time_interval['work_day']).dt.month
    # work_day_year
    df_cycle_time_interval['work_day_year']=pd.to_datetime(df_cycle_time_interval['work_day']).dt.year
    # concatenate year and week
    df_cycle_time_interval['work_year_week']=df_cycle_time_interval['work_day_year'].astype(str)+'-'+'W'+df_cycle_time_interval['work_day_week'].astype(str)
    # concatenate year and month
    df_cycle_time_interval['work_year_month']=df_cycle_time_interval['work_day_year'].astype(str)+'-'+'M'+df_cycle_time_interval['work_day_month'].astype(str)

    
    cycle_count= df_cycle_time_interval.groupby(['work_year_week','smooth_family'])['cycle_time'].mean().unstack().fillna(0).stack().reset_index()
    cycle_count['year']=cycle_count['work_year_week'].str.split('-W').str[0].astype(int)
    cycle_count['week']=cycle_count['work_year_week'].str.split('-W').str[1].astype(int)
    cycle_count=cycle_count.sort_values(by=['year','week']).reset_index() 
    week_cycle_count_axis_x=cycle_count['work_year_week'].unique()
    smooth_family= cycle_count['smooth_family'].unique()
    

    cycle_count_month= df_cycle_time_interval.groupby(['work_year_month','smooth_family'])['cycle_time'].mean().unstack().fillna(0).stack().reset_index()
    cycle_count_month['year']=cycle_count_month['work_year_month'].str.split('-M').str[0].astype(int)
    cycle_count_month['week']=cycle_count_month['work_year_month'].str.split('-M').str[1].astype(int)
    cycle_count_month=cycle_count_month.sort_values(by=['year','week']).reset_index()
    month_cycle_count_axis_x=cycle_count_month['work_year_month'].unique()
    smooth_family_month= cycle_count_month['smooth_family'].unique()
    


    ### for week 
    # list of colors
    colors_list=['#34a0a4','#023e8a','#e9c46a','#ffafcc','#2a9d8f','#e5989b','#e56b6f','#9e2a2b']
    # get colors for len smooth_family
    colors = [colors_list[color] for color in range(len(list(smooth_family)))]
    # dict of smooth_family(keys) and color (values)
    cycle_time_kpi.smooth_family=dict(zip(list(smooth_family),colors))
    cycle_time_kpi.cycle_count=cycle_count
    cycle_time_kpi.week_cycle_count_axis_x=week_cycle_count_axis_x
   
    ### for month
    colores_list_month=['#34a0a4','#023e8a','#e9c46a','#ffafcc','#2a9d8f','#e5989b','#e56b6f','#9e2a2b']
    # get colors for len smooth_family_month
    colors_month = [colores_list_month[color] for color in range(len(list(smooth_family_month)))]
    # dict of smooth_family_month(keys) and color (values)
    cycle_time_kpi.smooth_family_month=dict(zip(list(smooth_family_month),colors_month))
    cycle_time_kpi.cycle_count_month=cycle_count_month
    cycle_time_kpi.month_cycle_count_axis_x=month_cycle_count_axis_x
    


# calculate production plan (Freeze_end_date or smoothing_end_date) (week and month)
def production_plan_kpi(df_data):
    # date
    df_data['date_production']=np.where((df_data['Freeze_end_date'].isna()),(df_data['smoothing_end_date']),(df_data['Freeze_end_date']))
    # week of date date_production
    # df_data['dat_production_week']=np.where( (df_data['Freeze_end_date'].isna()),(pd.to_datetime(df_data['smoothing_end_date']).dt.week),(pd.to_datetime(df_data['Freeze_end_date']).dt.week)).astype(int)
    df_data['date_production_week']=np.where( (df_data['date_production'].isna()),(0),(pd.to_datetime(df_data['date_production']).dt.week)).astype(int)
    # month of date_production
    df_data['date_production_month']=np.where( (df_data['date_production'].isna()),(0),(pd.to_datetime(df_data['date_production']).dt.month)).astype(int)
    # year of date_production
    df_data['date_production_year']=np.where( (df_data['date_production'].isna()),(0),(pd.to_datetime(df_data['date_production']).dt.year)).astype(int)
    # concatenate year and week
    df_data['date_production_year_week']=df_data['date_production_year'].astype(str)+'-'+'W'+df_data['date_production_week'].astype(str)
    # concatenate year and month
    df_data['date_production_year_month']=df_data['date_production_year'].astype(str)+'-'+'M'+df_data['date_production_month'].astype(str)
    
    date_production_week=df_data.groupby(['date_production_year_week'])['id'].count().reset_index()
    date_production_month=df_data.groupby(['date_production_year_month'])['id'].count().reset_index()

   
   
    

    production_plan_kpi.date_production_week =date_production_week
    production_plan_kpi.date_production_month =date_production_month
    

# def planning(df_data):
#     # Program demand count per week
#     #Get week from date_end_plan if date_reordo is null or Get week from date_reordo
#     df_data['week_programm_demand']=np.where((df_data['date_reordo'].isna()),(pd.to_datetime(df_data['date_end_plan']).dt.week),(pd.to_datetime(df_data['date_reordo']).dt.week)).astype(int)
#     df_data['year_programm_demand']=np.where((df_data['date_reordo'].isna()),(pd.to_datetime(df_data['date_end_plan']).dt.year),(pd.to_datetime(df_data['date_reordo']).dt.year)).astype(int)
#     df_data.sort_values(by=['year_programm_demand','week_programm_demand'],inplace= True)
#     df_data['year_week_programm_demand']=df_data['year_programm_demand'].astype(str)+'-'+'W'+df_data['week_programm_demand'].astype(str)
#     df_data['week_programm_demand']=np.where((df_data['date_reordo'].isna()),(pd.to_datetime(df_data['date_end_plan']).dt.week),(pd.to_datetime(df_data['date_reordo']).dt.week)).astype(int)
    
#     #Program demand count per week
#     week_count=df_data.groupby('year_week_programm_demand')['id'].count().reset_index()
#     week_count['week_programm_demand']= df_data['week_programm_demand']
#     week_count['year_programm_demand']= df_data['year_programm_demand']
#     week_count.sort_values(by=['year_programm_demand','week_programm_demand'],inplace= True)
#     week_count['date_reordo']= df_data['date_reordo']
#     week_count['date_end_plan']= df_data['date_end_plan']
#     week_count['order_type']= df_data['order_type']
    
#     # week_count.to_csv('test1.csv')
#     # *********************************************************************************************************
    
    
#     #Demonstrated_capacity count per week
#     df_status=df_data[df_data['order_stat'].str.contains('TCLO|LIVR')]
#     df_status['year_week_end_date']=(pd.to_datetime(df_data['date_end_plan']).dt.year).astype(str)+'-'+'W'+(pd.to_datetime(df_data['date_end_plan']).dt.week).astype(str)
#     week_demonstrated_capacity_count=df_status.groupby('year_week_end_date')['id'].count().reset_index()
#     # week_demonstrated_capacity_count.to_csv('test2.csv')
    
#     #*********************************************************************************************************** 
    
#     # Production Plan count per week
#     # whene closed false
#     df_data_open =df_data[df_data['closed'] ==False]
#     # df_data_open.to_csv('open1.csv')    
#     # Get week from smoothing end date if freeze end date is null or Get week from freeze end date
#     df_data_open['week_production_plan']=np.where((df_data_open['Freeze_end_date'].isna()),(pd.to_datetime(df_data_open['smoothing_end_date']).dt.week),(pd.to_datetime(df_data_open['Freeze_end_date']).dt.week)).astype(int)
#     # df_data_open['week_production_plan']=np.where((df_data_open['Freeze_end_date'].isna()),df_data_open['smoothing_end_date'],False)
#     df_data_open['year_production_plan']=np.where((df_data_open['Freeze_end_date'].isna()),(pd.to_datetime(df_data_open['smoothing_end_date']).dt.year),(pd.to_datetime(df_data_open['Freeze_end_date']).dt.year)).astype(int)
#     df_data_open['year_week_production_plan']=df_data_open['year_production_plan'].astype(str)+'-'+'W'+df_data_open['week_production_plan'].astype(str) 
#     week_production_plan_count=df_data_open.groupby('year_week_production_plan')['id'].count().reset_index()
#     # week_production_plan_count.to_csv('test3.csv')
    
#     # ************************************************************************************************************
    
#     # Stock count per week
#     # get data 
#     zpp_stock =Zpp.objects.values('qte_available')
#     df_zpp_stock =pd.DataFrame(zpp_stock.values('qte_available'))

#     df_zpp_stock['year_week_programm_demand']=week_count['year_week_programm_demand']
#     df_zpp_stock['week_programm_demand_count']=week_count['id']
#     df_zpp_stock['year_week_production_plan']=week_production_plan_count['year_week_production_plan']
#     df_zpp_stock['week_production_plan_count']=week_production_plan_count['id']
#     # df_zpp_stock.to_csv('test4.csv')
#     return df_data
#     # df_zpp_stock['logistic_stock ']=( df_zpp_stock['qte_available'] + week_production_plan_count['id'].count() - week_production_plan_count['count'].count()) 
#     return render(request,'app/planning.html',{'records':df_data,'week_count':week_count,'week_demonstrated_capacity_count':week_demonstrated_capacity_count,'week_production_plan_count':week_production_plan_count})


#Test for web excel jquery
def data_table(request):
    return render(request,'app/Shopfloor/datatable.html') 

