# FINAL AUDIT REPORT: Text2SQL Model Performance

## Accuracy Summary (Result Match)

| Model                  |   PASS |   Total | Accuracy (%)   | Avg Speed (s)   |
|:-----------------------|-------:|--------:|:---------------|:----------------|
| Gemma-Base             |     18 |      20 | 90.0%          | 12.81s          |
| V1 (12k-Dataset)       |     19 |      20 | 95.0%          | 29.69s          |
| V2 (Context-Aligned)   |     15 |      20 | 75.0%          | 17.61s          |
| V3 (Spider-Specialist) |     18 |      20 | 90.0%          | 32.27s          |
| GPT-4o-mini (Cloud)    |     20 |      20 | 100.0%         | 2.07s           |

## Per-Question Deep Dive Analysis

### [gold_01] (EASY) What are the names of employees in the 'Sales' department?

**Expected SQL:** `SELECT name FROM employees WHERE department = 'Sales'`

| Model                  | Status   | Generated SQL                                            |
|:-----------------------|:---------|:---------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT name FROM employees WHERE department = 'Sales';` |
| V1 (12k-Dataset)       | PASS     | `SELECT name FROM employees WHERE department = 'Sales'`  |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM employees WHERE department = "Sales"`  |
| V3 (Spider-Specialist) | PASS     | `SELECT name FROM employees WHERE department = 'Sales'`  |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT name FROM employees WHERE department = 'Sales';` |

### [gold_02] (EASY) How many employees earn more than 50000?

**Expected SQL:** `SELECT COUNT(*) FROM employees WHERE salary > 50000`

| Model                  | Status   | Generated SQL                                           |
|:-----------------------|:---------|:--------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT COUNT(*)  FROM employees WHERE salary > 50000;` |
| V1 (12k-Dataset)       | PASS     | `SELECT COUNT(*) FROM employees WHERE salary > 50000`   |
| V2 (Context-Aligned)   | PASS     | `SELECT COUNT(id) FROM employees WHERE salary > 50000`  |
| V3 (Spider-Specialist) | PASS     | `SELECT COUNT(*) FROM employees WHERE salary > 50000`   |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT COUNT(*) FROM employees WHERE salary > 50000;`  |

### [gold_03] (EASY) List all project names with a budget over 100000.

**Expected SQL:** `SELECT name FROM projects WHERE budget > 100000`

| Model                  | Status   | Generated SQL                                      |
|:-----------------------|:---------|:---------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT name FROM projects WHERE budget > 100000;` |
| V1 (12k-Dataset)       | PASS     | `SELECT name FROM projects WHERE budget > 100000`  |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM projects WHERE budget > 100000`  |
| V3 (Spider-Specialist) | PASS     | `SELECT name FROM projects WHERE budget > 100000`  |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT name FROM projects WHERE budget > 100000;` |

### [gold_04] (EASY) Show the status of the 'Website Redesign' project.

**Expected SQL:** `SELECT status FROM projects WHERE name = 'Website Redesign'`

| Model                  | Status   | Generated SQL                                                                       |
|:-----------------------|:---------|:------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT status FROM projects WHERE name = 'Website Redesign';`                      |
| V1 (12k-Dataset)       | PASS     | `SELECT status FROM projects WHERE name = 'Website Redesign' AND budget > 0`        |
| V2 (Context-Aligned)   | PASS     | `SELECT status FROM projects WHERE name = "Website Redesign"`                       |
| V3 (Spider-Specialist) | PASS     | `SELECT * FROM projects WHERE name = 'Website Redesign' AND status = 'In Progress'` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT status FROM projects WHERE name = 'Website Redesign';`                      |

### [gold_05] (EASY) Show the average salary of all employees.

**Expected SQL:** `SELECT AVG(salary) FROM employees`

| Model                  | Status   | Generated SQL                        |
|:-----------------------|:---------|:-------------------------------------|
| Gemma-Base             | PASS     | `SELECT AVG(salary) FROM employees;` |
| V1 (12k-Dataset)       | PASS     | `SELECT AVG(salary) FROM employees`  |
| V2 (Context-Aligned)   | PASS     | `SELECT AVG(salary) FROM employees;` |
| V3 (Spider-Specialist) | PASS     | `SELECT AVG(salary) FROM employees`  |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT AVG(salary) FROM employees;` |

### [gold_06] (MEDIUM) List each department name and the number of doctors working there.

**Expected SQL:** `SELECT T2.name, COUNT(T1.id) FROM doctors AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id GROUP BY T2.name`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT d.name, COUNT(d.id) AS num_doctors FROM doctors d JOIN departments d2 ON d.dept_id = d2.id GR...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name, COUNT(*) FROM doctors AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id GROUP BY T1...` |
| V2 (Context-Aligned)   | PASS     | `SELECT d.name, COUNT(d.id) FROM departments AS d JOIN doctors AS do ON d.id = do.dept_id GROUP BY d....` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name, COUNT(*) FROM doctors AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id GROUP BY T1...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT d.name, COUNT(doc.id) AS doctor_count FROM departments d LEFT JOIN doctors doc ON d.id = doc....` |

### [gold_07] (MEDIUM) Show the names of patients who have more than 2 appointments.

**Expected SQL:** `SELECT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.id = T2.patient_id GROUP BY T1.name HAVING COUNT(T2.id) > 2`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT name FROM patients WHERE id IN (SELECT patient_id FROM appointments GROUP BY patient_id HAVIN...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.id = T2.patient_id GROUP BY T1.id H...` |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM patients WHERE id IN (SELECT patient_id FROM appointments GROUP BY patient_id HAVIN...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM patients AS T1 JOIN appointments AS T2 ON T1.id = T2.patient_id GROUP BY T2.pati...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT p.name FROM patients p WHERE p.id IN (SELECT a.patient_id FROM appointments a GROUP BY a.pati...` |

### [gold_08] (MEDIUM) Find the names of singers who have performed in at least 2 concerts.

**Expected SQL:** `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id GROUP BY T1.name HAVING COUNT(T2.concert_id) >= 2`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT s.name FROM singer s JOIN singer_in_concert sic ON s.id = sic.singer_id GROUP BY s.name HAVIN...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert A...` |
| V2 (Context-Aligned)   | ERROR    | `SELECT name FROM singer WHERE singer_in_concert.singer_id IN (SELECT singer_id FROM singer_in_concer...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert A...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT s.name FROM singer s JOIN singer_in_concert sic ON s.id = sic.singer_id GROUP BY s.name HAVIN...` |

### [gold_09] (MEDIUM) Show all car makers and the count of models they produce.

**Expected SQL:** `SELECT T1.maker, COUNT(T2.model_id) FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id = T2.maker GROUP BY T1.maker`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT maker, COUNT(*) AS model_count FROM model_list GROUP BY maker;`                                   |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.maker, COUNT(*) FROM model_list AS T1 JOIN car_makers AS T2 ON T1.maker = T2.id GROUP BY T...` |
| V2 (Context-Aligned)   | ERROR    | `SELECT COUNT(model_id) AS model_count FROM model_list WHERE maker = car_makers.id;`                      |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.maker, COUNT(*) FROM car_makers AS T1 JOIN model_list AS T2 ON T1.id = T2.maker GROUP BY T...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT cm.id, cm.maker, COUNT(ml.model_id) AS model_count FROM car_makers cm LEFT JOIN model_list ml...` |

### [gold_10] (MEDIUM) Show the name of the airline that has the most flights starting from 'JFK'.

**Expected SQL:** `SELECT T1.name FROM airlines AS T1 JOIN flights AS T2 ON T1.id = T2.airline WHERE T2.source = 'JFK' GROUP BY T1.name ORDER BY COUNT(*) DESC LIMIT 1`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT name FROM airlines JOIN flights ON airlines.id = flights.airline WHERE source = 'JFK' GROUP B...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM airlines AS T1 JOIN flights AS T2 ON T1.id = T2.airline WHERE T2.source = 'JFK' ...` |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM airlines JOIN flights ON airlines.id = flights.airline WHERE source = "JFK" GROUP B...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM airlines AS T1 JOIN flights AS T2 ON T1.id = T2.airline WHERE T2.source = 'JFK' ...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT a.name, COUNT(f.id) AS flight_count FROM airlines a, flights f WHERE a.id = f.airline AND f.s...` |

### [gold_11] (MEDIUM) Find the names of employees working in departments with a budget greater than 500000.

**Expected SQL:** `SELECT T1.name FROM employees AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id WHERE T2.budget > 500000`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT e.name FROM employees e JOIN departments d ON e.dept_id = d.id WHERE d.budget > 500000;`          |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM employees AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id WHERE T2.budget > 5...` |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM employees WHERE dept_id IN (SELECT id FROM departments WHERE budget > 500000)`          |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM employees AS T1 JOIN departments AS T2 ON T1.dept_id = T2.id WHERE T2.budget > 5...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT e.name FROM employees e WHERE e.dept_id IN (SELECT d.id FROM departments d WHERE d.budget > 5...` |

### [gold_12] (MEDIUM) What is the total revenue generate by the product 'iPhone'?

**Expected SQL:** `SELECT SUM(T1.price * T2.quantity) FROM products AS T1 JOIN sales AS T2 ON T1.id = T2.product_id WHERE T1.name = 'iPhone'`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | ERROR    | `SELECT SUM(quantity * price)  FROM sales WHERE product_id = (SELECT id FROM products WHERE name = 'i...` |
| V1 (12k-Dataset)       | PASS     | `SELECT SUM(quantity * price) FROM sales AS T1 JOIN products AS T2 ON T1.product_id = T2.id WHERE T2....` |
| V2 (Context-Aligned)   | ERROR    | `SELECT SUM(quantity * price) FROM sales WHERE product_id = (SELECT id FROM products WHERE name = "iP...` |
| V3 (Spider-Specialist) | ERROR    | `SELECT SUM(T1.quantity * T1.price) FROM products AS T1 JOIN sales AS T2 ON T1.id = T2.product_id WHE...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT SUM(s.quantity * p.price) AS total_revenue FROM sales s, products p WHERE s.product_id = p.id...` |

### [gold_13] (MEDIUM) List students who have an average grade above 85.

**Expected SQL:** `SELECT T1.name FROM students AS T1 JOIN grades AS T2 ON T1.id = T2.student_id GROUP BY T1.name HAVING AVG(T2.grade) > 85`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT s.name  FROM students s JOIN grades g ON s.id = g.student_id GROUP BY s.name HAVING AVG(g.gra...` |
| V1 (12k-Dataset)       | PASS     | `SELECT t1.name FROM students AS t1 JOIN grades AS t2 ON t1.id = t2.student_id GROUP BY t1.id HAVING ...` |
| V2 (Context-Aligned)   | PASS     | `SELECT AVG(grades.grade) FROM grades JOIN students ON grades.student_id = students.id WHERE grades.g...` |
| V3 (Spider-Specialist) | PASS     | `SELECT t1.id, t1.name FROM students AS t1 JOIN grades AS t2 ON t1.id = t2.student_id GROUP BY t1.id ...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT s.id, s.name FROM students s JOIN grades g ON s.id = g.student_id GROUP BY s.id, s.name HAVIN...` |

### [gold_14] (MEDIUM) How many books has each author written? List author name and count.

**Expected SQL:** `SELECT T2.name, COUNT(T1.id) FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.id GROUP BY T2.name`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT a.name, COUNT(b.id) AS book_count FROM authors a JOIN books b ON a.id = b.author_id GROUP BY ...` |
| V1 (12k-Dataset)       | ERROR    | `SELECT T1.name, COUNT(*) FROM books AS T1 JOIN authors AS T2 ON T1.author_id = T2.id GROUP BY T1.nam...` |
| V2 (Context-Aligned)   | PASS     | `SELECT AVG(authors.name) AS author_name, COUNT(books.id) AS total_books FROM authors JOIN books ON a...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name, COUNT(*) FROM authors AS T1 JOIN books AS T2 ON T1.id = T2.author_id GROUP BY T1.nam...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT authors.name, COUNT(books.id) AS book_count FROM authors LEFT JOIN books ON authors.id = book...` |

### [gold_15] (MEDIUM) Find customers who have a total balance across all accounts greater than 10000.

**Expected SQL:** `SELECT T1.name FROM customers AS T1 JOIN accounts AS T2 ON T1.id = T2.customer_id GROUP BY T1.name HAVING SUM(T2.balance) > 10000`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT c.name  FROM customers c JOIN accounts a ON c.id = a.customer_id WHERE a.balance > 10000;`        |
| V1 (12k-Dataset)       | PASS     | `SELECT t1.name FROM customers AS t1 JOIN accounts AS t2 ON t1.id = t2.customer_id GROUP BY t1.id HAV...` |
| V2 (Context-Aligned)   | PASS     | `SELECT AVG(balance) FROM accounts WHERE customer_id IN (SELECT id FROM customers) GROUP BY customer_...` |
| V3 (Spider-Specialist) | PASS     | `SELECT t1.id, t1.name FROM customers AS t1 JOIN accounts AS t2 ON t1.id = t2.customer_id GROUP BY t1...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT c.id, c.name FROM customers c JOIN accounts a ON c.id = a.customer_id GROUP BY c.id, c.name H...` |

### [gold_16] (HARD) List the names of singers who have performed in both 2024 and 2025 concerts.

**Expected SQL:** `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert AS T3 ON T2.concert_id = T3.id WHERE T3.year = 2024 INTERSECT SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert AS T3 ON T2.concert_id = T3.id WHERE T3.year = 2025`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT s.name  FROM singer s JOIN singer_in_concert sic ON s.id = sic.singer_id JOIN concert c ON si...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert A...` |
| V2 (Context-Aligned)   | ERROR    | `SELECT name FROM singer WHERE id IN (SELECT singer_id FROM singer_in_concert WHERE concert_id IN (SE...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM singer AS T1 JOIN singer_in_concert AS T2 ON T1.id = T2.singer_id JOIN concert A...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT s.name FROM singer s JOIN singer_in_concert sic ON s.id = sic.singer_id JOIN concert c ON sic...` |

### [gold_17] (HARD) What are the names of physicians who are not heads of any department?

**Expected SQL:** `SELECT name FROM physician WHERE id NOT IN (SELECT head FROM department)`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT name  FROM physician  WHERE id NOT IN (SELECT head FROM department);`                             |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM physician AS T1 JOIN department AS T2 ON T1.id = T2.head WHERE NOT T2.head = T1....` |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM physician WHERE id NOT IN (SELECT head FROM department)`                                |
| V3 (Spider-Specialist) | PASS     | `SELECT name FROM physician EXCEPT SELECT t1.name FROM physician AS t1 JOIN department AS t2 ON t1.id...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT name FROM physician WHERE id NOT IN (SELECT head FROM department);`                               |

### [gold_18] (HARD) List the models of cars produced by makers whose countries are in continent 1.

**Expected SQL:** `SELECT T1.model FROM model_list AS T1 JOIN car_makers AS T2 ON T1.maker = T2.id JOIN countries AS T3 ON T2.country = T3.id WHERE T3.continent = 1`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT model FROM model_list JOIN car_makers ON model_list.maker = car_makers.id JOIN countries ON c...` |
| V1 (12k-Dataset)       | PASS     | `SELECT t1.model_id FROM model_list AS t1 JOIN car_makers AS t2 ON t1.maker = t2.id JOIN countries AS...` |
| V2 (Context-Aligned)   | PASS     | `SELECT model_id FROM model_list WHERE maker IN (SELECT id FROM car_makers WHERE country IN (SELECT i...` |
| V3 (Spider-Specialist) | PASS     | `SELECT model_id FROM model_list WHERE maker IN (SELECT id FROM car_makers WHERE country = (SELECT id...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT ml.model_id, ml.maker, ml.model  FROM model_list ml  WHERE ml.maker IN (SELECT cm.id FROM car...` |

### [gold_19] (HARD) Show airline names that have flights from 'JFK' but NO flights to 'LAX'.

**Expected SQL:** `SELECT T1.name FROM airlines AS T1 JOIN flights AS T2 ON T1.id = T2.airline WHERE T2.source = 'JFK' EXCEPT SELECT T1.name FROM airlines AS T1 JOIN flights AS T3 ON T1.id = T3.airline WHERE T3.dest = 'LAX'`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | ERROR    | `SELECT name  FROM airlines  WHERE airline IN (SELECT airline FROM flights WHERE dest = 'LAX')    AND...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM airlines AS T1 JOIN flights AS T2 ON T1.id = T2.airline WHERE T2.source = 'JFK' ...` |
| V2 (Context-Aligned)   | ERROR    | `SELECT name FROM airlines WHERE airline IN (SELECT airline FROM flights WHERE source = "JFK" AND des...` |
| V3 (Spider-Specialist) | ERROR    | `SELECT name FROM airlines WHERE airline IN (SELECT DISTINCT airline FROM flights WHERE source = 'JFK...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT a.name  FROM airlines a  WHERE a.id IN (SELECT f.airline FROM flights f WHERE f.source = 'JFK...` |

### [gold_20] (HARD) Find the names of all instructors who work in a department with a budget higher than the average department budget.

**Expected SQL:** `SELECT name FROM instructor WHERE dept_name IN (SELECT dept_name FROM department WHERE budget > (SELECT AVG(budget) FROM department))`

| Model                  | Status   | Generated SQL                                                                                             |
|:-----------------------|:---------|:----------------------------------------------------------------------------------------------------------|
| Gemma-Base             | PASS     | `SELECT i.name FROM instructor i JOIN department d ON i.dept_name = d.dept_name WHERE d.budget > (SEL...` |
| V1 (12k-Dataset)       | PASS     | `SELECT T1.name FROM instructor AS T1 JOIN department AS T2 ON T1.dept_name = T2.dept_name WHERE T2.b...` |
| V2 (Context-Aligned)   | PASS     | `SELECT name FROM instructor WHERE dept_name IN (SELECT dept_name FROM department WHERE budget > (SEL...` |
| V3 (Spider-Specialist) | PASS     | `SELECT T1.name FROM instructor AS T1 JOIN department AS T2 ON T1.id = T2.dept_name WHERE T2.budget >...` |
| GPT-4o-mini (Cloud)    | PASS     | `SELECT name FROM instructor WHERE dept_name IN (SELECT dept_name FROM department WHERE budget > (SEL...` |

