







create database brandbook;
use brandbook;
/*
drop table profiles;
drop table users;*/

CREATE TABLE users
(
	id int NOT NULL AUTO_INCREMENT,
	nick varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	password_hash varchar(255) NOT NULL,
	created datetime NOT NULL,
	name varchar(50),
	surname varchar(50),
	CONSTRAINT users_primary_key PRIMARY KEY (id),
	UNIQUE (nick),
	UNIQUE (email)
);

CREATE TABLE profiles
(
	user_id int NOT NULL,
	last_change datetime NOT NULL,
	web varchar(255),
	user_profile varchar(100),
	job varchar(255),
	doing varchar(500),
	story varchar(10000),
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE chat_messages
(
	user_id int NOT NULL,
	created time NOT NULL,
	message varchar(1000) NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE wall_messages
(
	id int NOT NULL AUTO_INCREMENT,
	user_id int NOT NULL,
	created datetime NOT NULL,
	message varchar(1000) NOT NULL,
	CONSTRAINT wall_messages_primary_key PRIMARY KEY (id),
	FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE wall_comments
(
	id int NOT NULL AUTO_INCREMENT,
	wall_message_id int NOT NULL,
	user_id int NOT NULL,
	created datetime NOT NULL,
	message varchar(1000) NOT NULL,
	CONSTRAINT wall_comments_primary_key PRIMARY KEY (id),
	FOREIGN KEY (user_id) REFERENCES users(id),
	FOREIGN KEY (wall_message_id) REFERENCES wall_messages(id)
);
