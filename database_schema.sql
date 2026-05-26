CREATE DATABASE IF NOT EXISTS bristol_buzz
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE bristol_buzz;

DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(80) NOT NULL UNIQUE,
    category_description VARCHAR(255)
);

CREATE TABLE venues (
    venue_id INT AUTO_INCREMENT PRIMARY KEY,
    venue_name VARCHAR(120) NOT NULL,
    address_line VARCHAR(160) NOT NULL,
    city VARCHAR(80) NOT NULL DEFAULT 'Bristol',
    postcode VARCHAR(12) NOT NULL,
    map_url VARCHAR(500),
    UNIQUE (venue_name, postcode)
);

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    venue_id INT NOT NULL,
    event_title VARCHAR(160) NOT NULL,
    event_description TEXT NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    price_label VARCHAR(60) NOT NULL,
    image_url VARCHAR(500),
    CONSTRAINT fk_events_category
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_events_venue
        FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    attendee_name VARCHAR(120) NOT NULL DEFAULT '',
    attendee_email VARCHAR(255) NOT NULL DEFAULT '',
    attendee_phone VARCHAR(30),
    ticket_quantity INT NOT NULL DEFAULT 1,
    special_requests VARCHAR(500),
    booking_status VARCHAR(30) NOT NULL DEFAULT 'confirmed',
    payment_status VARCHAR(30) NOT NULL DEFAULT 'accepted',
    payment_reference VARCHAR(40),
    booked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_bookings_event
        FOREIGN KEY (event_id) REFERENCES events(event_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

INSERT INTO categories (category_name, category_description) VALUES
('Family Friendly', 'Events suitable for families and visitors of all ages.'),
('Music', 'Concerts, festivals, and live music events.'),
('Arts and Culture', 'Theatre, opera, light shows, and cultural activities.'),
('Food and Drink', 'Food markets, tasting events, and local produce festivals.'),
('Sport', 'Running, fitness, and competitive community events.');

INSERT INTO venues (venue_name, address_line, city, postcode, map_url) VALUES
('Ashton Court Estate', 'Long Ashton', 'Bristol', 'BS41 9JN', 'https://www.google.com/maps?q=Ashton+Court+Estate,+Long+Ashton,+Bristol+BS41+9JN'),
('Bristol Harbourside', 'Harbourside', 'Bristol', 'BS1 5DB', 'https://www.google.com/maps?q=Bristol+Harbour,+Bristol'),
('Bristol Hippodrome', 'St Augustine''s Parade', 'Bristol', 'BS1 4UZ', 'https://www.google.com/maps?q=Bristol+Hippodrome,+St+Augustine%27s+Parade,+Bristol+BS1+4UZ'),
('Millennium Square', 'Explore Lane', 'Bristol', 'BS1 5SZ', 'https://www.google.com/maps?q=Millennium+Square,+Bristol'),
('Bristol City Centre', 'Broadmead and Old City', 'Bristol', 'BS1 1HQ', 'https://www.google.com/maps?q=Bristol+City+Centre'),
('Theatre Royal Bristol', 'King Street', 'Bristol', 'BS1 4ED', 'https://www.google.com/maps?q=The+Theatre+Royal,+Bristol');

INSERT INTO events
(category_id, venue_id, event_title, event_description, event_date, start_time, price_label, image_url)
VALUES
(1, 1, 'International Balloon Fiesta', 'Europe''s largest annual meeting of hot air balloons.', '2026-08-07', '18:00:00', 'Free entry', 'assets/events/balloon-fiesta.jfif'),
(2, 2, 'Love Saves The Day', 'A Bristol music festival with national and local performers.', '2026-05-23', '12:00:00', 'Tickets live', 'assets/events/music-festival.jfif'),
(3, 5, 'Bristol Light Festival', 'A winter evening light trail with glowing installations and family-friendly walking routes.', '2026-11-27', '17:30:00', 'Free trail', 'assets/events/light-festival.jfif'),
(3, 3, 'Opera: La Boheme', 'Puccini opera performance with English surtitles.', '2026-06-19', '19:30:00', 'Ticketed', 'assets/events/opera.jfif'),
(4, 2, 'Bristol Food Festival', 'Street food, cooking demonstrations, and local producers around the harbour.', '2026-07-11', '11:00:00', 'Food and drink', 'assets/events/food-festival.jfif'),
(3, 6, 'Bristol Comedy Festival', 'Stand-up comedy featuring established comedians and Bristol talent.', '2026-08-22', '19:30:00', 'Comedy night', 'assets/events/comedy-night.jfif'),
(5, 4, 'Great Bristol Half Marathon', 'A city running event with half marathon and 10k options.', '2026-05-10', '09:00:00', 'Registration required', 'assets/events/half-marathon.jfif');
