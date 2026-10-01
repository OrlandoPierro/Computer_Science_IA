CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,
								 username VARCHAR(255) NOT NULL,
                                 password_hash VARCHAR(255) NOT NULL);

CREATE TABLE IF NOT EXISTS subjects(subject_id INTEGER PRIMARY KEY,
									subject_name VARCHAR(50) NOT NULL,
                                    level VARCHAR(2) NOT NULL
                                    CHECK(level IN ("HL","SL")),
                                    total_topics INTEGER NOT NULL
                                    CHECK(total_topics > 0));
                                    
CREATE TABLE IF NOT EXISTS user_subjects(user_subject_id INTEGER PRIMARY KEY,
										 user_id INTEGER NOT NULL,
                                         subject_id INTEGER NOT NULL,
                                         target_grade INTEGER NOT NULL
                                         CHECK(target_grade BETWEEN 1 TO 7),
                                         
                                         FOREIGN KEY (user_id) REFERENCES users(user_id),
                                         FOREIGN KEY (subject_id) REFERENCES subjects(subject_id));
                                         
CREATE TABLE IF NOT EXISTS assessments(assessment_id INTEGER PRIMARY KEY,
									   user_subject_id INTEGER NOT NULL,
                                       assessment_type VARCHAR(20) NOT NULL
                                       CHECK(assessment_type IN 
                                       ("Learning Experience","Formative","Summative","Mock Exam","IA"),
                                       score DECIMAL NOT NULL
                                       CHECK(score >= 0),
                                       maximum_score DECIMAL NOT NULL
                                       CHECK(maximum_score > 0),
                                       assessment_date DATE NOT NULL,
                                       topics_covered_count INTEGER NOT NULL
                                       CHECK(topic_covered_count > 0),
                                       
                                       CHECK(score <= maximum_score)
                                       FOREIGN KEY (user_subject_id) REFERENCES user_subjects(user_subject_id));
                                       
CREATE TABLE IF NOT EXISTS grade_boundaries(boundary_id INTEGER PRIMARY KEY, 
											subject_id INTEGER NOT NULL,
                                            exam_year YEAR NOT NULL,
                                            exam_session VARCHAR(8) NOT NULL
                                            CHECK(exam_session IN ("May", "November")),
                                            grade INTEGER NOT NULL
                                            CHECK(grade BETWEEN 1 TO 7),
                                            lower_boundary DECIMAL NOT NULL
                                            CHECK(lower_boundary BETWEEN 0 TO 100),
                                            
                                            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id));
                                            
                                            