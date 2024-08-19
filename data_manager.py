from typing import Final, List, Tuple
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()
TOKEN: Final[str] = os.getenv("NOTION_TOKEN")
URL: Final[str] = f"https://api.notion.com"

headers = {
    'Authorization': TOKEN,
    'Notion-Version' : "2021-05-11"
}

# retrieves database info for given database id
def query_db(id) -> List[map]:
    db_id = id
    DB_QUERY: Final[str] = f"{URL}/v1/databases/{db_id}/query"

    response = requests.post(url=DB_QUERY, headers=headers)
    print(response.status_code)
    data = response.json()
    rows = data["results"]

    return rows


# the following functions are used to retrieve a list containing the repspective property of all entries

def get_times() -> List[Tuple[str, str]]:

    LESSON_DB_ID = os.getenv("LESSONS_DATABASE")

    rows = query_db(LESSON_DB_ID)

    res = []

    for row in rows:
        times = row['properties']['Time']['title'][0]['text']['content'].split("-")
        res.append((times[0], times[1]))
    
    return res

def get_dates() -> List[str]:

    LESSON_DB_ID = os.getenv("LESSONS_DATABASE")

    rows = query_db(LESSON_DB_ID)

    res = []

    for row in rows:
        date = row['properties']['Date']['date']['start']
        res.append(date)
    
    return res

def get_students() -> list[str]:

    STUDENT_DB_ID = os.getenv("STUDENTS_DATABASE")

    rows = query_db(STUDENT_DB_ID)

    res = []
    
    for row in rows:
        name = row['properties']['Full Name']['title'][0]['text']['content']
        formatted_name = name.replace(" ", "").lower()
        res.append(formatted_name)
    
    return res

# the following functions are used the update the database

def add_student(f: str, l: str) -> str:

    # check if the given student is already in the list of students
    
    formatted_name = f.lower() + l.lower()
    
    if formatted_name in get_students():
        print("Student is already in database!")
        return "Registered"

    # if not, add them
    
    CREATE_PAGE: Final[str] = f"{URL}/v1/pages"
    PARENT: Final[str] = os.getenv("STUDENTS_DATABASE")

    first = f.title()
    last = l.title()

    data = {
        'parent': {'database_id': PARENT},
        'properties': {
            'Last': {
                'id': 'Y`y}',
                'type': 'rich_text',
                'rich_text': [
                    {
                    'type': 'text',
                    'text': {
                        'content': last,
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': last,
                    'href': None
                    }
                ]
            },
            'First': {
                'id': 'kg\\U',
                'type': 'rich_text',
                'rich_text': [
                    {
                    'type': 'text',
                    'text': {
                        'content': first,
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': first,
                    'href': None
                    }
                ]
            },
            'Full Name': {
                'id': 'title',
                'type': 'title',
                'title': [
                    {
                    'type': 'text',
                    'text': {
                        'content': f'{first} {last}',
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': f'{first} {last}',
                    'href': None
                    }
                ]
            }
        }
    }

    response = requests.post(url=CREATE_PAGE, json=data, headers=headers)
    id = response.json()['id']

    with open('/Users/vincent/Actual Projects/Discord Bot/student_IDs.txt', mode='a') as file:
        file.write(f'{first} {last}={id}\n')
        file.flush()
    
    return id
    

def add_lesson(start: str, end: str, date: str, subject: str, topic: str, student_id: str) -> int:
    
    IDS: list[str] = []

    with open('student_IDs.txt', mode='r') as file:
        for line in file:
            IDS.append(line.split('=')[1].strip())

    if student_id.strip() not in IDS:
        return -2

    # 2 methods only used in this function
    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    def ranges_overlap(start1, end1, start2, end2, buffer=0) -> bool:
        start1_minutes = time_to_minutes(start1)
        end1_minutes = time_to_minutes(end1)
        start2_minutes = time_to_minutes(start2)
        end2_minutes = time_to_minutes(end2)

        buffered_start2_minutes = start2_minutes - buffer
        bufferd_end2_minutes = end2_minutes + buffer

        if start1_minutes > end1_minutes or start2_minutes > end2_minutes:
            print("Invalid time")
            return False

        return max(start1_minutes, buffered_start2_minutes) < min(end1_minutes, bufferd_end2_minutes)

    # office hours for tutoring
    tutor_date = datetime.strptime(date, "%Y-%m-%d").weekday()
    if tutor_date >= 5:
        office_start = "12:30"
        office_end = "18:30"
    elif tutor_date < 5 and tutor_date % 2 == 0:
        office_start = "00:00"
        office_end = "00:00"
    else:
        office_start = "16:00"
        office_end = "20:00"

    # If office hours are "00:00 to 00:00", do not allow scheduling
    if office_start == "00:00" and office_end == "00:00":
        print('No office hours available today!')
        return -3
    
    # check if the time is booked
    times = get_times()
    dates = get_dates()

    # Otherwise, check for conflicts with both office hours and existing appointments
    for i in range(len(times)):
        existing_time = times[i]
        existing_date = dates[i]
        
        if (ranges_overlap(existing_time[0], existing_time[1], start, end, buffer=10) and date == existing_date) or not ranges_overlap(office_start, office_end, start, end):
            print('This time is unavailable!')
            return -1
    
    # if not, add the lesson to the database
    CREATE_PAGE: Final[str] = f"{URL}/v1/pages"
    PARENT: Final[str] = os.getenv("LESSONS_DATABASE")

    data = {
        'parent': {'database_id': PARENT},
        'properties': {
            'Student': {
                'id': '=MYi',
                'type': 'relation',
                'relation': [
                    {
                    'id': student_id
                    }
                ],
                'has_more': False
            },
            'Topic': {
                'id': 'EKXy',
                'type': 'rich_text',
                'rich_text': [
                    {
                    'type': 'text',
                    'text': {
                        'content': topic,
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': topic,
                    'href': None
                    }
                ]
            },
            'Subject': {
                'id': 'iYP>',
                'type': 'rich_text',
                'rich_text': [
                    {
                    'type': 'text',
                    'text': {
                        'content': subject,
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': subject,
                    'href': None
                    }
                ]
            },
            'Date': {
                'id': 'n_IU',
                'type': 'date',
                'date': {
                    'start': date,
                    'end': None,
                    'time_zone': None
                }
            },
            'Time': {
                'id': 'title',
                'type': 'title',
                'title': [
                    {
                    'type': 'text',
                    'text': {
                        'content': f'{start}-{end}',
                        'link': None
                    },
                    'annotations': {
                        'bold': False,
                        'italic': False,
                        'strikethrough': False,
                        'underline': False,
                        'code': False,
                        'color': 'default'
                    },
                    'plain_text': f'{start}-{end}',
                    'href': None
                    }
                ]
            }
        }
    }
    
    requests.post(url=CREATE_PAGE, json=data, headers=headers)
    return 1