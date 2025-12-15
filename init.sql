CREATE TABLE IF NOT EXISTS departments (
    id INT PRIMARY KEY,
    name TEXT NOT NULL,
    max_simultaneous_vacations INT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    full_name TEXT NOT NULL,
    department_id INT REFERENCES departments(id),
    manager_id VARCHAR REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vacation_balances (
    user_id VARCHAR REFERENCES users(id),
    year INT NOT NULL,
    total_days INT NOT NULL,
    used_days INT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, year)
);

CREATE TABLE IF NOT EXISTS vacation_requests (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    comment TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS request_history (
    id VARCHAR PRIMARY KEY,
    request_id VARCHAR REFERENCES vacation_requests(id),
    action TEXT NOT NULL,
    comment TEXT,
    acted_by VARCHAR REFERENCES users(id),
    acted_at TIMESTAMP NOT NULL
);

INSERT INTO departments (id, name, max_simultaneous_vacations) VALUES
    (1, 'Development', 2),
    (0, 'HR', 1)
ON CONFLICT DO NOTHING;

INSERT INTO users (id, login, password, role, full_name, department_id, manager_id) VALUES
    ('u2', 'bob', 'password', 'manager', 'Bob Petrov', 1, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO users (id, login, password, role, full_name, department_id, manager_id) VALUES
    ('u1', 'alice', 'password', 'employee', 'Alice Ivanova', 1, 'u2'),
    ('u3', 'carol', 'password', 'hr', 'Carol Sidorova', 0, NULL)
ON CONFLICT DO NOTHING;

INSERT INTO vacation_balances (user_id, year, total_days, used_days) VALUES
    ('u1', EXTRACT(YEAR FROM CURRENT_DATE), 28, 0),
    ('u2', EXTRACT(YEAR FROM CURRENT_DATE), 28, 0),
    ('u3', EXTRACT(YEAR FROM CURRENT_DATE), 28, 0)
ON CONFLICT DO NOTHING;

INSERT INTO vacation_requests (
    id, user_id, start_date, end_date, type, status, comment, created_at
) VALUES (
    'req_demo',
    'u1',
    CURRENT_DATE + INTERVAL '7 day',
    CURRENT_DATE + INTERVAL '9 day',
    'annual',
    'pending',
    'Family trip',
    NOW()
)
ON CONFLICT DO NOTHING;
