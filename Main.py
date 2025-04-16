import requests
import json
import time
from recap_token import RecaptchaSolver

class TicketBooking:
    def __init__(self, user_data_file, recaptcha_token):
        self.s = requests.Session()
        self.wait = 0
        self.recaptcha_token = recaptcha_token
        self.load_user_data(user_data_file)
        self.teams = self.initialize_teams()
        self.match_id = None
        self.category_id = None
        self.team_id = None
        self.match_team_zone_id = None
        self.price = None

    def load_user_data(self, user_data_file):
        with open(user_data_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
            self.username, self.password, self.search_word, self.seats, self.category = lines[:5]

    def initialize_teams(self):
        return {
            'زمالك': {'team_name': 'الزمالك', 'eng_team': 'Zamalek SC', 'teamid': '79'},
            'اهلي': {'team_name': 'الأهلي', 'eng_team': 'Al Ahly FC', 'teamid': '77'},
            'مصر': {'team_name': 'المصري', 'eng_team': 'Al-Masry SC', 'teamid': '182'}
        }

    def find_team_info(self):
        for key, team_info in self.teams.items():
            if key in self.search_word:
                self.team_name = team_info['team_name']
                self.eng_team = team_info['eng_team']
                self.team_id = team_info['teamid']
                return
        raise ValueError("Team not found in search word!")

    def get_headers(self):
        return {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

    def get_match_id(self):
        url = 'https://tazkarti.com/data/matches-list-json.json'
        res = self.s.get(url, headers=self.get_headers()).json()
        for match in res:
            if self.eng_team in [match['teamName1'], match['teamName2']]:
                if match.get('matchStatus') == 1:
                    self.match_id = match['matchId']
                    return
        raise ValueError("Match ID not found!")

    def get_ticket_info(self):
        url = f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{self.match_id}.json'
        res = self.s.get(url, headers=self.get_headers()).json()
        for category in res['data']:
            if category['categoryName'].strip().lower() == self.category.strip().lower():
                self.category_id, self.match_team_zone_id, self.price = category['categoryId'], category['matchTeamzoneId'], category['price']
                return
        raise ValueError("Category not found!")

    def login_and_book_tickets(self):
        login_url = 'https://tazkarti.com/home/Login'
        json_data = {'Username': self.username, 'Password': self.password, 'recaptchaResponse': self.recaptcha_token}
        res = self.s.post(login_url, headers=self.get_headers(), json=json_data).json()
        token = res.get('access_token')
        if not token:
            raise ValueError("Login failed!")
        self.book_seats(token)

    def book_seats(self, token):
        book_url = 'https://tazkarti.com/booksprt/BookingTickets/addSeats'
        json_data = {
            'stadiumId': 1, 'matchId': int(self.match_id), 'teamId': int(self.team_id),
            'lockedSeatsList': [{'categoryId': int(self.category_id), 'countSeats': int(self.seats), 'price': self.price, 'matchTeamZoneId': int(self.match_team_zone_id)}]
        }
        headers = self.get_headers()
        headers['Authorization'] = f'Bearer {token}'
        res = self.s.post(book_url, headers=headers, json=json_data).json()
        if 'seatGuid' in res:
            print("Booking successful!")
        else:
            print("Booking failed, retrying...")
            time.sleep(5)
            self.book_seats(token)

if __name__ == '__main__':
    solver = RecaptchaSolver('YOUR_RECAPTCHA_URL')
    tok = solver.get_token()
    booking = TicketBooking(r'C:\Users\mohamed\Desktop\Auto-Booking-Tazkarti-Ticket-0.2/data.txt', tok)
    booking.find_team_info()
    booking.get_match_id()
    booking.get_ticket_info()
    booking.login_and_book_tickets()
