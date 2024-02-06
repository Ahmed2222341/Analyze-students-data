import json
from googletrans import Translator
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

with open("datascience.json", "r") as file:
    datascience = json.load(file)

with open("robotics.json", "r") as file:
    robotics = json.load(file)

with open("multimedia.json", "r") as file:
    multimedia = json.load(file)

def save(_file, data):
    with open(_file, "w") as file:
        json.dump(data, file, indent=2)

# Set up Chrome options to run headless (without opening a visible browser window)
chrome_options = Options()
chrome_options.add_argument('--headless')

# Start Chrome browser
driver = webdriver.Chrome(options=chrome_options)

# Function to translate the name
def translate_name(name):
    translator = Translator()
    translation = translator.translate(name, src='ar', dest='en')
    return translation.text
def get_data(start_seat_no, end_seat_no, letter, department, file):
    seat_no = start_seat_no

    while seat_no <= end_seat_no:
        url = f'http://app1.helwan.edu.eg/Computer{letter}/HasasnUpMlist.asp?z_sec=LIKE&z_gro=%3D&z_dep=%3D&z_st_name=LIKE&z_st_settingno=%3D&x_st_settingno={seat_no}&x_st_name=&psearch=&Submit=++++%C8%CD%CB++++'

        # Load the webpage
        driver.get(url)

        # Get the page source
        html_source = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_source, 'html.parser')
        # print(soup)
        a_tags = soup.find_all('a')
        a_on_line_294 = a_tags[-1]
        href_value = a_on_line_294.get('href')
        std_code = href_value.split('=')[-1]

        if std_code == "reset":  # this will happen if the seat number is not found
            print(f"Couldn't store the data for the seat number: '{seat_no}' (seat number not found)")
            seat_no += 1
            continue
        else:
            url = f"http://app1.helwan.edu.eg/Computer{letter}/HasasnUpMview.asp?StdCode={std_code}"
            driver.get(url)
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, 'html.parser')

            # store name (translated in english) and full mark
            arabic_name = driver.find_element(By.XPATH, "/html/body/form/div/table[1]/tbody/tr[3]/td[2]/div/font/b").text
            name = translate_name(arabic_name)
            full_mark = int(driver.find_element(By.XPATH, "/html/body/form/div/table[4]/tbody/tr[3]/td[1]/div/font/b").text)

            # get marks
            td_elements = soup.find_all('td', {'width': '100'})  # Find all <td> elements with width="100"
            int_values = []
            for td in td_elements:
                text_content = td.text.strip()
                integers = re.findall(r'\d+', text_content)  # Extract integers using regular expression
                int_values.extend(map(int, integers))  # Convert extracted strings to integers and add to the list

            langs = ["English", "Social Issues", "IS", "Discrete Math", "CS", "Mathematics"]
            marks_dict = {}
            for i in range(len(langs)):
                marks_dict[langs[i]] = int_values[i]

            # store gpa
            gpa = driver.find_element(By.XPATH, "/html/body/form/div/table[4]/tbody/tr[3]/td[6]/div/font/b")
            if gpa.text != "":
                gpa = float(gpa.text)
            else:
                gpa = 0.0

            # get rating
            gpa_ranges = {1: "Very Weak", 2: "Weak", 2.5: "Acceptable", 3: "Good", 3.5: "Very Good"}
            for threshold, value in gpa_ranges.items():
                if gpa < threshold:
                    rating = value
                    break
            else:
                rating = "Excellent"

            # store the data
            data = {
                "Seat Number": seat_no,
                "Name": name,
                "Marks": marks_dict,
                "Full Mark": full_mark,
                "GPA": gpa,
                "Rating": rating
            }

            department.append(data)
            save(file, department)
            print(f"Stored the data for the seat number: '{seat_no}' successfully")

            seat_no += 1

## Uncomment these to scrape the data from the website
# get_data(231051001, 231051369, "C", datascience, "datascience.json")
# get_data(231052001, 231052233, "B", robotics, "robotics.json")
# get_data(231053001, 231053108, "A", multimedia, "multimedia.json")


# after scraping the data, analyze it
# function to analyze departments and write to the file
def write_department_info(file, department_name, department):
    with open(file, 'w') as f:
        f.write(f"\n========= {department_name} Students' data ========= \n\n")
        f.write(f"Number of students in this department: {len(department)}\n")

        highest_student = max(department, key=lambda student: student["GPA"])
        f.write(f"Highest GPA in {department_name} department: {highest_student['GPA']}, Seat number: {highest_student['Seat Number']}, Name: {highest_student['Name']}, Mark: {highest_student['Full Mark']}\n")

        average_gpa = round(sum(student["GPA"] for student in department) / len(department), 2)
        f.write(f"Average GPA in {department_name} department: {average_gpa}\n\n")

        ratings = [student["Rating"] for student in department]
        rating_counts = {rating: ratings.count(rating) for rating in set(ratings)}
        for rating, count in rating_counts.items():
            f.write(f"Number of students with '{rating}' rating: {count}\n")

# analyze subjects
def analyze_subjects(students_data):
    subject_marks = {
        "English": [],
        "Social Issues": [],
        "IS": [],
        "Discrete Math": [],
        "CS": [],
        "Mathematics": []
    }
    for student in students_data:
        marks = student["Marks"]
        for subject, mark in marks.items():
            if mark >= 95:
                subject_marks[subject].append("higher than 95")
            elif 85 <= mark <= 95:
                subject_marks[subject].append("85-95")
            elif 70 <= mark <= 75:
                subject_marks[subject].append("70-75")
            elif 45 <= mark < 50:
                subject_marks[subject].append("45-50")
            elif mark < 50:
                subject_marks[subject].append("Failed")
            else:
                subject_marks[subject].append(f"{mark}-{mark+5}")
    return subject_marks

def analyze_students(students_data):
    failed_count = [sum(1 for mark in student["Marks"].values() if mark < 50) for student in students_data]
    return [failed_count.count(i) for i in range(max(failed_count) + 1)]

def calculate_money_earned(subject_failure_counts):
    credit_hours = {"English": 2, "Social Issues": 2, "IS": 3, "Discrete Math": 3, "CS": 3, "Mathematics": 3}
    price_per_credit_hour = 1400
    money_earned_per_subject = {subject: credit_hours[subject] * price_per_credit_hour * subject_failure_counts[subject] for subject in subject_failure_counts}
    total_money_earned = sum(money_earned_per_subject.values())
    return money_earned_per_subject, total_money_earned

def calculate_average_mark_in_subject(students_data, subject):
    marks = [student["Marks"][subject] for student in students_data if student["Marks"][subject] > 0]
    return int(sum(marks) / len(marks))

# write to files
def write_subject_analysis(file, subject_analysis, students_data):
    with open(file, "a") as f:
        f.write("\n\nSubject Analysis:\n")
        for subject, marks in subject_analysis.items():
            f.write(f"\n{subject}:\n")
            grades = {"50-55": 50, "45-50": 45, "70-75": 70, "85-95": 85, "higher than 95": 95, "Failed": 0}
            grade_counts = {grade: marks.count(grade) for grade in grades}
            for grade, count in grade_counts.items():
                f.write(f"\tNumber of students with mark {grade}: {count}\n")

            average_mark = calculate_average_mark_in_subject(students_data, subject)
            f.write(f"\tAverage mark in {subject}: {average_mark}\n")

def write_student_analysis(file, student_analysis):
    with open(file, "a") as f:
        f.write("\nStudent Analysis:\n")
        for i, count in enumerate(student_analysis):
            f.write(f"Number of students failed in {i} subjects: {count}\n")

def write_failed_subjects_analysis(file, sorted_subjects, subject_failure_counts):
    with open(file, "a") as f:
        f.write("\nSubjects arranged by the number of failed students:\n")
        for subject in sorted_subjects:
            f.write(f"{subject}: {subject_failure_counts[subject]} failed students\n")

def write_money_earned(file, money_earned_per_subject, total_money_earned):
    with open(file, "a") as f:
        f.write("\nMoney earned from each subject:\n")
        for subject, money_earned in money_earned_per_subject.items():
            money_earned_str = '{:,.0f}'.format(money_earned)  # Formatting with comma for thousands separator
            f.write(f"{subject}: {money_earned_str}\n")
        total_money_earned_str = '{:,.0f}'.format(total_money_earned)  # Formatting with comma for thousands separator
        f.write(f"\nTotal money earned from all subjects: {total_money_earned_str}\n")

# Analyze departments and write to the file
file_path = "info.txt"
departments = [datascience, robotics, multimedia]
department_names = ["Data Science", "Robotics", "Multi Media"]
for department, department_name in zip(departments, department_names):
    write_department_info(file_path, department_name, department)

faculty = sum(departments, [])
write_department_info(file_path, "Faculty of CS", faculty)

# Analyze subjects
students_data = sum(departments, [])
subject_analysis = analyze_subjects(students_data)
write_subject_analysis(file_path, subject_analysis, students_data)

# Analyze students
student_analysis = analyze_students(students_data)
write_student_analysis(file_path, student_analysis)

# Arrange subjects by the number of failed students
subject_failure_counts = {subject: subject_analysis[subject].count("Failed") for subject in subject_analysis}
sorted_subjects = sorted(subject_failure_counts, key=subject_failure_counts.get, reverse=True)
write_failed_subjects_analysis(file_path, sorted_subjects, subject_failure_counts)

# Calculate money earned by the faculty
money_earned_per_subject, total_money_earned = calculate_money_earned(subject_failure_counts)
write_money_earned(file_path, money_earned_per_subject, total_money_earned)

