CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    subject VARCHAR(50) NOT NULL,
    grade NUMERIC(3, 1) NOT NULL
);

INSERT INTO students (first_name, last_name) VALUES 
('Jan', 'Kowalski'), 
('Anna', 'Nowak');

INSERT INTO grades (student_id, subject, grade) VALUES 
(1, 'Matematyka', 4.5), 
(1, 'Fizyka', 3.0),
(2, 'Biologia', 5.0);