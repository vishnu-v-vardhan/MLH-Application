from flask import render_template, redirect, url_for, request, render_template_string, jsonify, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import app, db, Users, UserActivity, department_form_list, designations,Csr_Activity, FunctionHalls, NumOfDeaths, Retirements 
import os
from werkzeug.utils import secure_filename
from datetime import datetime, date
from flask import send_file

login_manager = LoginManager(app)
login_manager.login_view = 'login'

"""Files for CSR activity"""
upload_folder26 = os.path.join('static/csr','upload_file_csr_path')
os.makedirs(upload_folder26, exist_ok=True)

"""Files for No Of Death Cases"""
upload_folder27 = os.path.join('static/nod','upload_office_order_path')
os.makedirs(upload_folder27, exist_ok=True)

# Project Code Generation - Common to all forms
def generate_unique_id(dept, sub_dept, table):
    ### Generating Project Code for MM - Disposal ###
    ProjectCode = ""

    # Automatic Start Date capture - Production
    start_date = date.today()

    # To check if there is at least 1 entry in the DB or not
    first_entry = table.query.first()
    lastRow = str(table.query.order_by(table.id.desc()).first().id) if first_entry else None

    # Format Date in lastRow from String to Date Object
    prev_date = datetime.strptime(lastRow[7:15], "%d%m%Y").date() if lastRow != None else None 

    # If today > latest date that is already existing in DB - For first entry of today
    if first_entry == None or start_date > prev_date:
        ProjectCode = f"{dept}{sub_dept}{start_date.strftime('%d%m%Y')}001"
    
    # Subsequent entries for the same date
    elif start_date == prev_date:
        ProjectCode = f"{dept}{sub_dept}{start_date.strftime('%d%m%Y')}{str(int(lastRow[16:19]) + 1).zfill(3)}"

    return ProjectCode

def log_user_activity(user_id, user_name, user_department, route_name, activity_done):
    if user_id:
        user_activity = UserActivity(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            user_name=user_name,
            user_department=user_department,
            route_name=route_name,
            activity_done=activity_done
        )
        db.session.add(user_activity)
        db.session.commit()

""" Login """
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).filter_by(id=int(user_id)).first()

@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Users.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            flash('User successfully logged in', 'success')
            # Redirect to the appropriate landing page based on the user's department
            if user.department == 'welfare':
                return redirect(url_for('landing_page_welfare'))
            else:
                return redirect(url_for('login'))

        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))  # Redirect back to login page with flashed messages
    else:
        # Clear any existing flashed messages before rendering the login page
        if 'message' in session:
            session.pop('message')
        return render_template('login.html')


""" Landing Page """

@app.route('/landing_page_welfare',methods=['POST', 'GET'])
@login_required
def landing_page_welfare():
    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    return render_template('form_listout_welfare.html', user=current_user, form_names=form_names)

@app.route('/action_landing_page_welfare/', methods=['POST', 'GET'])
@login_required
def landing_page_welfare_action():
    filter_value = request.form.get('filter')
    print('Route accessed!')
    if request.method == 'POST':
        projects = []

        form_table = {
            "csr": "Csr_Activity",
            "function halls": "FunctionHalls",
            "number of deaths": "NumOfDeaths",
            "retirements": "Retirements"
        }

        if filter_value in form_table:
            class_name = form_table[filter_value]
            print("Filter Value: ", filter_value)
            projects = globals()[class_name].query.all()
        else:
            projects = []
    projects_json = []
    for project in projects:
        project_data = {}
        for column in project.__table__.columns:
            project_data[column.name] = getattr(project, column.name)
        projects_json.append(project_data)

    response_data = {'filter_value': filter_value, 'projects': projects_json}

    return jsonify(response_data)

"""-----------CSR Starts-------------------"""

@app.route('/csr', methods=['POST', 'GET'])
@login_required
def csr_activity():
    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = 'Accessed an Csr_Activity creation page'  

    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    return render_template('CSR.html', user=current_user,form_names=form_names) 

@app.route('/submit_csr_activity', methods=['POST'])
@login_required 
def submit_csr_activity():
    if request.method=='POST':

        project_code = generate_unique_id('GAD', 'CSRA', Csr_Activity)

        # Log the user activity
        user_id = current_user.id if current_user.is_authenticated else None
        user_name = current_user.name if current_user.is_authenticated else None
        user_department = current_user.department if current_user.is_authenticated else None
        route_name = request.endpoint  
        activity_done = f'Created an Csr_Activity Form Entry with ID: {project_code}'    
        log_user_activity(user_id, user_name, user_department, route_name, activity_done)


        # Get Files
        upload_file_csr = request.files.get('Upload_File_Csr') #file
        upload_file_csr_path = None

        if upload_file_csr:
            upload_file_csr_path = os.path.join(upload_folder26, f"{project_code}_{secure_filename(upload_file_csr.filename)}")
            upload_file_csr.save(upload_file_csr_path)
            upload_file_csr_path = upload_file_csr_path.replace('\\', '/')

        date_csr = request.form.get('Date_Csr')  #date
        activity_name_csr = request.form.get('Activity_Name_Csr')
        amount_proposed_csr = request.form.get('Amount_Proposed_Csr') 
        amount_sanctioned_csr = request.form.get('Amount_Sanctioned_Csr')
        sanctioned_party_name_csr = request.form.get('Sanctioned_Party_Name_Csr')
        sanctioned_date_csr = request.form.get('Sanctioned_Date_Csr')
        notified_date_csr = request.form.get('Notified_Date_Csr')
        approved_finance_csr = request.form.get('Approved_Finance_Csr')
        approval_date_csr = request.form.get('Approval_Date_Csr')

        remarks_gad_csr = request.form.getlist('Remarks_GAD_Csr') #Dynamic
        remarks_gad_csr_str = ','.join(remarks_gad_csr)

        remarks_finance_csr = request.form.get('Remarks_Finance_Csr')

        new_entry = Csr_Activity(
             id = project_code,
             date_csr = date_csr or None,
             activity_name_csr = activity_name_csr,
             amount_proposed_csr = amount_proposed_csr or 0,
             upload_file_csr_path = upload_file_csr_path,
             amount_sanctioned_csr = amount_sanctioned_csr or 0,
             sanctioned_party_name_csr = sanctioned_party_name_csr,
             sanctioned_date_csr = sanctioned_date_csr or None,
             notified_date_csr = notified_date_csr or None,
             approved_finance_csr = approved_finance_csr,
             approval_date_csr = approval_date_csr or None,
             remarks_gad_csr = remarks_gad_csr_str,
             remarks_finance_csr = remarks_finance_csr
         )

        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))


@app.route('/edit_csr_activity/<csr_id>', methods=['POST', 'GET'])
@login_required
def edit_csr_activity(csr_id):
    csr_entry = Csr_Activity.query.get_or_404(csr_id)

     # Log the user activity
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Edited an Csr_Activity Form of ID: {csr_id}'  
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)


    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    if request.method =='POST':
        upload_file_csr = request.files.get('Upload_File_Csr') #file
        
        upload_file_csr_path = None

        project_code = csr_entry.id
        
        if upload_file_csr:
            upload_file_csr_path = os.path.join(upload_folder26, f"{project_code}_{secure_filename(upload_file_csr.filename)}")
            upload_file_csr.save(upload_file_csr_path)
            upload_file_csr_path = upload_file_csr_path.replace('\\', '/')
        else:
            upload_file_csr_path = csr_entry.upload_file_csr_path
        
        csr_entry.date_csr = request.form.get('Date_Csr') or None #date
        csr_entry.activity_name_csr = request.form.get('Activity_Name_Csr')
        csr_entry.amount_proposed_csr = request.form.get('Amount_Proposed_Csr') or 0 #number 
        csr_entry.amount_sanctioned_csr = request.form.get('Amount_Sanctioned_Csr') or 0 #number
        csr_entry.sanctioned_party_name_csr = request.form.get('Sanctioned_Party_Name_Csr')
        csr_entry.sanctioned_date_csr = request.form.get('Sanctioned_Date_Csr') or None #date
        csr_entry.upload_file_csr_path = upload_file_csr_path
        csr_entry.notified_date_csr = request.form.get('Notified_Date_Csr') or None #date
        csr_entry.approved_finance_csr = request.form.get('Approved_Finance_Csr')
        csr_entry.approval_date_csr = request.form.get('Approval_Date_Csr') or None #date
        
        remarks_gad_csr_data = request.form.getlist('Remarks_GAD_Csr')
        csr_entry.remarks_gad_csr = ','.join(remarks_gad_csr_data)

        csr_entry.remarks_finance_csr = request.form.get('Remarks_Finance_Csr')
        
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))
    
    remarks_gad_csr = csr_entry.remarks_gad_csr.split(',')
    remarks_gad_csr_list = [remark for remark in remarks_gad_csr]

    return render_template('CSR_Edit.html', Csr_Activity=csr_entry, remarks_gad = remarks_gad_csr_list, user=current_user, form_names=form_names) 


    
@app.route('/delete_csr_activity/<csr_id>', methods=['GET'])
@login_required
def delete_csr_activity(csr_id):
    csr_entry = Csr_Activity.query.get(csr_id)

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Deleted the Csr_Activity form of ID: {csr_id}'  

    # Log the user activity
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    if csr_entry:
        csr_entry.deleted = 1
        db.session.commit()
    return redirect(url_for('landing_page_welfare'))
"""---------------CSR Ends----------------"""

"""--------------- FunctionHalls Starts -------------"""

@app.route('/function halls', methods=['POST', 'GET'])
@login_required
def functionHalls():
    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = 'Accessed an FunctionHalls creation page'  

    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    return render_template('FunctionHalls.html', user=current_user,form_names=form_names) 

@app.route('/submit_functionHalls', methods=['POST'])
@login_required
def submit_functionHalls():
    if request.method=='POST':
        project_code = generate_unique_id('GAD', 'FUNH', FunctionHalls)

        # Log the user activity
        user_id = current_user.id if current_user.is_authenticated else None
        user_name = current_user.name if current_user.is_authenticated else None
        user_department = current_user.department if current_user.is_authenticated else None
        route_name = request.endpoint  
        activity_done = f'Created an FunctionHalls Form Entry with ID: {project_code}'    
        log_user_activity(user_id, user_name, user_department, route_name, activity_done)



        function_hall_name = request.form.get('Function_Hall_Name') 
        alloted_to_party_name = request.form.get('Alloted_To_Party_Name') 
        free_allotment = request.form.get('Free_Allotment')
        reason_for_free_allotment = request.form.get('Reason_For_Free_Allotment')
        revenue_rs = request.form.get('Revenue_Rs')


        new_entry = FunctionHalls(
            id = project_code,
            function_hall_name = function_hall_name, 
            alloted_to_party_name =  alloted_to_party_name,
            free_allotment = free_allotment, 
            reason_for_free_allotment = reason_for_free_allotment, 
            revenue_rs = revenue_rs or 0,   
        )



        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))
    
@app.route('/edit_functionHalls/<fh_id>', methods=['POST', 'GET'])
@login_required
def edit_functionHalls(fh_id):
    fh_entry = FunctionHalls.query.get_or_404(fh_id)

     # Log the user activity
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Edited an FunctionHalls Form of ID: {fh_id}'  
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)


    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    if request.method =='POST':
       fh_entry.function_hall_name = request.form.get('Function_Hall_Name') 
       fh_entry.alloted_to_party_name = request.form.get('Alloted_To_Party_Name') 
       fh_entry.free_allotment = request.form.get('Free_Allotment')
       fh_entry.reason_for_free_allotment = request.form.get('Reason_For_Free_Allotment')
       fh_entry.revenue_rs = request.form.get('Revenue_Rs')
    
       db.session.commit()

       return redirect(url_for('landing_page_welfare'))
    return render_template('FunctionHalls_Edit.html', functionHalls=fh_entry, user=current_user, form_names=form_names)


@app.route('/delete_functionHalls/<fh_id>', methods=['GET'])
@login_required
def delete_functionHalls(fh_id):
    fh_entry = FunctionHalls.query.get(fh_id)

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Deleted the FunctionHalls form of ID: {fh_id}'  

    # Log the user activity
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    if fh_entry:
        fh_entry.deleted = 1
        db.session.commit()
    return redirect(url_for('landing_page_welfare'))


"""--------------- FunctionHalls Ends -------------"""

"""--------------------Num Of Deaths Starts-------------------------"""

@app.route('/number of deaths', methods=['POST', 'GET'])
@login_required
def numOfDeaths():
    options_designations = designations.query.all()
    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = 'Accessed an Num Of Deaths creation page'  

    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    return render_template('NumOfDeaths.html', user=current_user,form_names=form_names, options_designations = options_designations) 
    

@app.route('/submit_numOfDeaths', methods=['POST'])
@login_required
def submit_numOfDeaths():
   if request.method=='POST':
        
        project_code = generate_unique_id('GAD', 'DTHS', NumOfDeaths)

        # Log the user activity
        user_id = current_user.id if current_user.is_authenticated else None
        user_name = current_user.name if current_user.is_authenticated else None
        user_department = current_user.department if current_user.is_authenticated else None
        route_name = request.endpoint  
        activity_done = f'Created an Num Of Deaths Form Entry with ID: {project_code}'    
        log_user_activity(user_id, user_name, user_department, route_name, activity_done)

        #get files
        upload_office_order = request.files.get('Upload_Office_Order') #file
        upload_office_order_path = None
       
        if upload_office_order:
             upload_office_order_path = os.path.join(upload_folder27, f"{project_code}_{secure_filename(upload_office_order.filename)}")
             upload_office_order.save(upload_office_order_path)
             upload_office_order_path = upload_office_order_path.replace('\\', '/')

      

        concerned_department = request.form.get('Concerned_Department') 
        post_category = request.form.get('Post_Category') 
        employee_code = request.form.get('Employee_Code') 
        designation = request.form.get('Designation')
        retirement_date = request.form.get('Retirement_Date')
        employee_name = request.form.get('Employee_Name')
        payscale = request.form.get('Payscale')
        date_of_settlement = request.form.get('Date_of_Settlement')
        num_of_death_cases = request.form.get('Num_of_Death_Cases')
        # action_taken_document = request.files.get('Action_Taken_Document')
        
        
        new_entry = NumOfDeaths(
            id = project_code,
            concerned_department = concerned_department or None,
            post_category = post_category or None,
            employee_code = employee_code or None,
            designation = designation or None,
            retirement_date = retirement_date or None,
            upload_office_order_path = upload_office_order_path or None,
            employee_name = employee_name or None,
            payscale = payscale or None,
            date_of_settlement = date_of_settlement or None,
            num_of_death_cases = num_of_death_cases or 0
           
        )

        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))

@app.route('/edit_numOfDeaths/<nod_id>', methods=['POST', 'GET'])
@login_required
def edit_numOfDeaths(nod_id):
    nod_entry = NumOfDeaths.query.get_or_404(nod_id)
    options_designations = designations.query.all()

    # Log the user activity
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Edited an Num of Deaths Form of ID: {nod_id}'  
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)


    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    if request.method =='POST':
        upload_office_order = request.files.get('Upload_Office_Order') #file
        upload_office_order_path = None

        project_code = nod_entry.id

        if upload_office_order:
            upload_office_order_path = os.path.join(upload_folder27, f"{project_code}_{secure_filename(upload_office_order.filename)}")
            upload_office_order.save(upload_office_order_path)
            upload_office_order_path = upload_office_order_path.replace('\\', '/')
        else:
            upload_office_order_path = nod_entry.upload_office_order_path
        
        nod_entry.concerned_department = request.form.get('Concerned_Department') or None
        nod_entry.post_category = request.form.get('Post_Category') or None
        nod_entry.employee_code = request.form.get('Employee_Code') or None
        nod_entry.designation = request.form.get('Designation') or None
        nod_entry.retirement_date = request.form.get('Retirement_Date') or None
        nod_entry.employee_name = request.form.get('Employee_Name') or None
        nod_entry.payscale = request.form.get('Payscale') or None
        nod_entry.date_of_settlement = request.form.get('Date_of_Settlement') or None
        nod_entry.num_of_death_cases = request.form.get('Num_of_Death_Cases') or 0
        nod_entry.upload_office_order_path = upload_office_order_path or None

        db.session.commit()

        return redirect(url_for('numOfDeaths'))
    return render_template('NumOfDeaths_edit.html', NumOfDeaths = nod_entry, options_designations=options_designations, user=current_user, form_names=form_names) 

@app.route('/delete_nod/<nod_id>', methods=['GET'])
@login_required
def delete_numOfDeaths(nod_id):
    nod_entry = NumOfDeaths.query.get_or_404(nod_id)

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Deleted the Num Of Deaths form of ID: {nod_id}'  

    # Log the user activity
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    if nod_entry:
        nod_entry.deleted = 1
        db.session.commit()
    return redirect(url_for('landing_page_welfare'))

"""-------------------------- Num Of Deaths Ends---------------------"""

"""-------------------------- Retirements starts---------------------"""

@app.route('/retirements', methods=['POST', 'GET'])
@login_required
def retirements():
    
    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = 'Accessed an Retirements creation page'  

    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    return render_template('Retirements.html', user=current_user,form_names=form_names)

@app.route('/get_designations', methods=['POST', 'GET'])
def get_designations():
    if request.method == 'POST':
        options_designations = designations.query.all()
        projects_json = []
        for option in options_designations:
            project_data = {
                'title': getattr(option, 'title')
            }
            projects_json.append(project_data)

        response_data = {'options': projects_json}
        return jsonify(response_data)


@app.route('/submit_Retirements', methods=['POST'])
@login_required
def submit_retirements():
    if request.method=='POST':

        project_code = generate_unique_id('GAD', 'RTRM', Retirements)

        # Log the user activity
        user_id = current_user.id if current_user.is_authenticated else None
        user_name = current_user.name if current_user.is_authenticated else None
        user_department = current_user.department if current_user.is_authenticated else None
        route_name = request.endpoint  
        activity_done = f'Created an Retirements Form Entry with ID: {project_code}'    
        log_user_activity(user_id, user_name, user_department, route_name, activity_done)
 
        concerned_department = request.form.get('Concerned_Department_Retirements') 
        post_category = request.form.get('Post_Category_Retirements') 
        employee_code = request.form.get('Employee_Code_Retirements')
        employee_name = request.form.get('Employee_Name_Retirements')
        designation = request.form.get('Designation_Retirements')
        payscale = request.form.get('Payscale_Retirements') 
        retirement_date = request.form.get('Retirement_Date_Retirements')
        residing_in_port_quaters = request.form.get('Residing_Port_Quaters_Retirements')
        remarks_by_gad = request.form.get('Remarks_By_GAD_Retirements')
        remarks_by_finance = request.form.get('Remarks_Finance_Retirements')
        
        new_entry = Retirements(
            id = project_code,
            concerned_department = concerned_department or None, 
            post_category =  post_category or None,
            employee_code = employee_code or None, 
            employee_name = employee_name or None, 
            designation = designation or None,
            payscale = payscale or None,
            retirement_date = retirement_date or None,
            residing_in_port_quaters = residing_in_port_quaters or None, 
            remarks_by_gad = remarks_by_gad or None, 
            remarks_by_finance = remarks_by_finance or None,
        )



        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))

@app.route('/edit_retirements/<rt_id>', methods=['POST', 'GET'])
@login_required
def edit_retirements(rt_id):
    rt_entry = Retirements.query.get_or_404(rt_id)
    #options_designations = designations.query.all()

    # Log the user activity
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Edited an Retirements Form of ID: {rt_id}'  
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)


    user_department_id = current_user.department_id
    form_names = department_form_list.query.filter_by(department_id=user_department_id).all()

    if request.method =='POST':
        rt_entry.concerned_department = request.form.get('Concerned_Department_Retirements')  or None
        rt_entry.post_category = request.form.get('Post_Category_Retirements')  or None
        rt_entry.employee_code = request.form.get('Employee_Code_Retirements') or None
        rt_entry.employee_name = request.form.get('Employee_Name_Retirements') or None
        rt_entry.designation = request.form.get('Designation_Retirements') or None
        rt_entry.payscale = request.form.get('Payscale_Retirements')  or None
        rt_entry.retirement_date = request.form.get('Retirement_Date_Retirements') or None
        rt_entry.residing_in_port_quaters = request.form.get('Residing_In_Port_Quaters_Retirements') or None
        rt_entry.remarks_by_gad = request.form.get('Remarks_By_GAD_Retirements') or None
        rt_entry.remarks_by_finance = request.form.get('Remarks_By_Finance_Retirements') or None
        
        db.session.commit()

        return redirect(url_for('landing_page_welfare'))
    return render_template('Retirements_edit.html', Retirements=rt_entry, user=current_user, form_names=form_names)

@app.route('/delete_rt/<rt_id>', methods=['GET'])
@login_required
def delete_retirements(rt_id):
    rt_entry = Retirements.query.get_or_404(rt_id)

    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.name if current_user.is_authenticated else None
    user_department = current_user.department if current_user.is_authenticated else None
    route_name = request.endpoint  
    activity_done = f'Deleted the Retirements form of ID: {rt_id}'  

    # Log the user activity
    log_user_activity(user_id, user_name, user_department, route_name, activity_done)

    if rt_entry:
        rt_entry.deleted = 1
        db.session.commit()
    return redirect(url_for('landing_page_welfare'))

"""-------------------------- Retirements ends---------------------""" 

@app.route('/logout')
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('login'))

@app.route('/view_file/<form>/<file_type>/<id>', methods=['GET'])
@login_required
def view_file(form, file_type, id):
    form_table = {
            "csr": "Csr_Activity",
            "function halls": "FunctionHalls",
            "number of deaths": "NumOfDeaths",
            "retirements": "Retirements"
        }

    if form in form_table:
        class_name = form_table[form]
        filePath = globals()[class_name].query.get_or_404(id)

    file_path = getattr(filePath, f'{file_type}_path')
    absolute_file_path = os.path.join(file_path)
    if os.path.exists(absolute_file_path):
        return send_file(absolute_file_path, mimetype='application/pdf')
    else:
        return "File not found", 404

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port = 8081)