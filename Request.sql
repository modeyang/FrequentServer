
SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

use test;
DROP TABLE IF EXISTS userRequest;
CREATE TABLE userRequest (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user VARCHAR(50) NOT NULL ,
    action VARCHAR(20) NOT NULL,
    content VARCHAR(500) NOT NULL,
    updated TIMESTAMP NOT NULL,
    counts INT);

-- alert table userRequest change column title content varchar(500);
insert into userRequest(user, action, content, updated, counts) values ('ygs', 'reply', 'fdas', '2013-03-19 13:30:23', 1)
