# Burak757 Seat Booking System
# Apache Airlines - Seat Management Application
# Author: [Your Name]
# Description: Manages seat bookings for the Burak757 aircraft

"""
First Steps:
Initialize the seating plan for the Burak757.
'F' = Free seat, 'R' = Reserved seat, 'X' = Aisle, 'S' = Storage
Rows 1-80, Columns A, B, C, (X), D, E, F

Next:
Create the functions that will check availability, book seats, and free seats respectively

"""


"""
This code has been refactored so as to answer Part B of the questions set for the project

"""

import random

import string
# string will give me tools to pick random characters; that way I wouldn't have to waste time on typing them out manually, and I'd avoid typos

import sqlite3
# this is a built-in library for working with SQLite databases


""" PART B ADDITION: Database setup """
# Creates a SQLite database file (apache_bookings.db) with
# a 'bookings' table to store passenger details per booking

def setup_database():
    conn = sqlite3.connect("apache_bookings.db")
# sqlite3.connect() either opens the database file if it exists, or creates it fresh if it doesn't
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_ref   TEXT PRIMARY KEY,
            passport_no   TEXT NOT NULL,
            first_name    TEXT NOT NULL,
            last_name     TEXT NOT NULL,
            seat_row      INTEGER NOT NULL,
            seat_col      TEXT NOT NULL
        )
    """)
# CREATE TABLE IF NOT EXISTS is important; without the IF NOT EXISTS part, it would crash every time after the first run because the table already exists
    conn.commit()
    conn.close()



""" PART B ADDITION: Booking reference generator """
# Algorithm:
#   1. Pool of characters = digits 0-9 + uppercase letters A-Z (36 total)
#   2. Randomly sample 8 characters from the pool (no repeats within one ref)
#   3. Join into a single string
#   4. Check the database to confirm the reference doesn't already exist
#   5. If it does exist, repeat from step 2 until a unique ref is found
# The chance of collision is extremely low (36^8 possible references)
# but the uniqueness check guarantees correctness regardless.

def generate_booking_ref():
    conn = sqlite3.connect("apache_bookings.db")
    cursor = conn.cursor()
    
# combine uppercase letters and digits into one pool string of 36 characters
    pool = string.ascii_uppercase + string.digits  # A-Z and 0-9
    
    while True:
# Step 2-3: Randomly pick 8 characters and return them as a list, then join them
        ref = ''.join(random.sample(pool, 8))

# Step 4: Check uniqueness against the database
        cursor.execute("SELECT booking_ref FROM bookings WHERE booking_ref = ?", (ref,))
        if cursor.fetchone() is None:
# Step 5: Reference is unique, we can use it
            conn.close()
            return ref

"""
The while loop handles the uniqeuness requirement.
We query the database to check if that reference already exists
cursor.fetchone() returns None if no match is found, meaning it's unique and safe to use.
If it did already exist, the loop just runs again and generates a new one.

"""


def initialize_seats():
    seats = {}
    
    for row in range(1, 81):
        for col in ['A', 'B', 'C']:
# Free seats
            seats[f"{row}{col}"] = 'F'
       
# Aisle (not bookable)
        seats[f"{row}X"] = 'X'
       
# Rows 77-78 cols D,E,F are Storage
        if row in range(77, 79):
            for col in ['D', 'E', 'F']:
                seats[f"{row}{col}"] = 'S'
        else:
            for col in ['D', 'E', 'F']:
                seats[f"{row}{col}"] = 'F'   # Free seats
    
    return seats


# Check if a specific seat is available for booking
def check_availability(seats, seat_id):
    seat_id = seat_id.upper()
    if seat_id not in seats:
        return "invalid"
    status = seats[seat_id]
    if status == 'F':
        return "seat available"
    elif status == 'R':
        return "seat reserved"
    elif status == 'X':
        return "aisle"
    elif status == 'S':
        return "storage"
# If status is a booking reference (Part B edit), treat as reserved
    else:
        return "seat reserved"
    
    
"""
The next function shall:
Book a seat if it is free.
Returns True if booking was successful, False otherwise.
"""

def book_seat(seats, seat_id):
    seat_id = seat_id.upper()
    availability = check_availability(seats, seat_id)
    
# the aisles, reserved seats, and storage areas should not be bookable
    if availability == "seat available":

# Collect passenger details [.strip() is just used to remove unnecessary spaces]
        print("Please enter passenger details:")
        passport_no = input("  Passport number: ").strip()
        first_name  = input("  First name: ").strip()
        last_name   = input("  Last name: ").strip()

# Generate a unique booking reference
        booking_ref = generate_booking_ref()

# Store the booking reference in the seat (replaces 'R')
        seats[seat_id] = booking_ref

# Save passenger details to the database
        seat_row = int(''.join(filter(str.isdigit, seat_id)))  # extract row number
        seat_col = ''.join(filter(str.isalpha, seat_id))       # extract column letter
        
        """
        Instead of storing 'R', we now store the actual booking reference string directly in the seats dictionary.
        This means we can always trace which reference belongs to which seat.
        
        To insert into the database we need the row number and column letter separately.
        We extract them from the seat_id string using filter():
        
        filter(str.isdigit, seat_id) keeps only the digit characters
        filter(str.isalpha, seat_id) keeps only the letter characters
        
        """
        conn = sqlite3.connect("apache_bookings.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bookings (booking_ref, passport_no, first_name, last_name, seat_row, seat_col)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (booking_ref, passport_no, first_name, last_name, seat_row, seat_col))
        conn.commit()
        conn.close()
        
# The '?' placeholders in the SQL INSERT are important — they prevent SQL injection.

        print(f"✓ Seat {seat_id} successfully booked.")
        print(f"  Your booking reference is: {booking_ref}")
        return True
    
    elif availability == "seat reserved":
        print(f"✗ Seat {seat_id} is already booked.")
    elif availability == "aisle":
        print(f"✗ {seat_id} is an aisle — cannot be booked.")
    elif availability == "storage":
        print(f"✗ {seat_id} is a storage area — cannot be booked.")
    else:
        print(f"✗ Seat {seat_id} does not exist.")
    return False


# This next function will be used to free a previously booked seat


def free_seat(seats, seat_id):
    seat_id = seat_id.upper()
    current = seats.get(seat_id)
    
# The function will only free a seat if it was previously reserved; if it was already free, nothing would change
    
# A booked seat now holds a booking reference (not just 'R')
# so we check it's not F, X, or S to confirm it was booked
    if current not in (None, 'F', 'X', 'S'):
        booking_ref = current

# Remove the passenger record from the database
        conn = sqlite3.connect("apache_bookings.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE booking_ref = ?", (booking_ref,))
        conn.commit()
        conn.close()
# We grab the reference from the seat, use it to DELETE the matching row from the database, then reset the seat back to 'F'.
# This keeps the dictionary and the database in sync.

# Restore seat to free
        seats[seat_id] = 'F'
        print(f"✓ Seat {seat_id} has been freed. Booking reference {booking_ref} has been removed.")
    else:
        print(f"✗ Seat {seat_id} is not currently booked.")
        



# The next funcion is the function that will display the full seating plan with current statuses
def show_booking_status(seats):
    
    print("\n--- Burak757 Seating Plan ---")
# I shall make the display look very cool and organised so maybe I'll get extra marks :)
    print(f"{'Row':<5} {'A':<4} {'B':<4} {'C':<4} {'|':<3} {'D':<4} {'E':<4} {'F':<4}")
    print("-" * 40)
# time to actually show the booking status; we're going for an output that ends up looking like a visual map of the plane
    for row in range(1, 81):
        a = seats[f"{row}A"]
        b = seats[f"{row}B"]
        c = seats[f"{row}C"]
        d = seats.get(f"{row}D", 'S')
        e = seats.get(f"{row}E", 'S')
        f = seats.get(f"{row}F", 'S')
# seats now store booking refs instead of 'R', so display 'R' for any booked seat
        def display(val):
            return val if val in ('F', 'X', 'S') else 'R'
        print(f"{row:<5} {display(a):<4} {display(b):<4} {display(c):<4} {'|':<3} {display(d):<4} {display(e):<4} {display(f):<4}")
# This shows the status of all seating positions on the plane in the format of a map of the plane



# as an extra function (question 5), I wll add a function that shows a summary of free, reserved and unavailable seats
def booking_summary(seats):
    free = 0
    reserved = 0
    unavailable = 0  # Counts X (aisle) and S (storage)

    for status in seats.values():
        if status == 'F':
            free += 1
        elif status == 'X' or status == 'S':
            unavailable += 1
        else:
# anything else is a booking reference, so it counts as reserved
            reserved += 1     # replaces the old elif status == 'R'
            
    print("\n===== Booking Summary =====")
    print(f"Free seats:       {free}")
    print(f"Reserved seats:   {reserved}")
    print(f"Unavailable:      {unavailable}  (aisles/storage)")

# Now to create a function for the main menu that will run until the user exits
def main_menu(seats):
    while True:
        
# print out a list of options that the user will have the option of choosing between
        print("\n===== Apache Airlines Booking System =====")
        print(" \n1. Check seat availability 2. Book a seat 3.Free a seat 4.Show all seat statuses 5.Display a booking summary 6.Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
# we connect all the options presented to the user to their corresponding functions
        if choice == '1':
            seat = input("Enter seat ID (e.g. 10A): ")
            result = check_availability(seats, seat)
            print(f"Seat {seat.upper()} status: {result}")
        elif choice == '2':
            seat = input("Enter seat to book (e.g. 10A): ")
            book_seat(seats, seat)
        elif choice == '3':
            seat = input("Enter seat to free (e.g. 10A): ")
            free_seat(seats, seat)
        elif choice == '4':
            show_booking_status(seats)
        elif choice == '5':
            booking_summary(seats)
        elif choice == '6':
            print("Thanks for flying with Apache Airlines! Goodbye!") # nice message that prints on exit
            break
        
# in order to make sure the user understands they can only enter numbers between 1 and 6, we show this error message before looping back to the choices they have
        else:
            print("Invalid choice. Please enter 1-6.")
        
setup_database()
seats = initialize_seats()
main_menu(seats)
