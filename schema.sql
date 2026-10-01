CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,
								 username VARCHAR(20),
                                 password_hash VARCHAR(20))

CREATE TABLE IF NOT EXISTS subjects(subject_id INTEGER UNIQUE PRIMARY KEY,
									subject_name VARCHAR(20),
                                    level VARCHAR(20),
                                    total_topic INTEGER)
                                    
CREATE TABLE IF NOT EXISTS user_subjects(user_subject_id INTEGER UNIQUE PRIMARY KEY,
										 user_id INTEGER,
                                         subject_id INTEGER,
                                         target_grade INTEGER)
                                         
CREATE TABLE IF NOT EXISTS assessments(assessment_id INTEGER UNIQUE PRIMARY KEY,
									   user_subject_id INTEGER,
                                       assessment_type VARCHAR(20),
                                       score DECIMAL,
                                       maximum_score DECIMAL,
                                       assessment_date DATE,
                                       topic_covered_count INTEGER)
                                       
CREATE TABLE IF NOT EXISTS grade_boundaries(boundary_id INTEGER UNIQUE PRIMARY KEY, 
											subject_id INTEGER,
                                            exam_year YEAR,
                                            exam_session VARCHAR(8),
                                            grade INTEGER,
                                            lower_boundary DECIMAL)
                                            
                                            