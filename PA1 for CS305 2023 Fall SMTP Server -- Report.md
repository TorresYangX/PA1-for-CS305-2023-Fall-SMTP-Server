# PA1 for CS305 2023 Fall: SMTP Server -- Report

**Sid: 12112729**

**Name: 杨烜**

##  Screenshot of the result of the testing script

![image-20231029192049358](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231029192049358.png)

## Screenshot of the Wireshark packets(Only run 4.yml)

- POP3

  ![image-20231029200505427](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231029200505427.png)

- SMTP

  ![image-20231029200631855](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231029200631855.png)




# Advanced function

### Error handling

-  **Connection refused**

![image-20231030150443191](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030150443191.png)

![image-20231030145955976](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030145955976.png)

when the username and password don't match, sent a error message to agent.

- **illegal mail address**

![image-20231030150413521](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030150413521.png)

![image-20231030150225757](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030150225757.png)

when there is no valid receptor, send a error message to agent.

![image-20231030150711866](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030150711866.png)

![image-20231030150619605](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030150619605.png)

when the sender's address is invalid, send a error message to agent

- **illegal command**

  - when there isn't mail in the mailbox and ```retr```:

    ![image-20231030151036423](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030151036423.png)

  - when  ``retr x`` and x is not a number(same as ``list x `` and ``dele x``):

    ![image-20231030153047735](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030153047735.png)

    ![image-20231030153016258](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030153016258.png)

    

### More commands

``Help``:

modify the ``agent.py``:

![image-20231030153824744](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030153824744.png)

modify the ``server.py``:

![image-20231030153847511](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030153847511.png)

![image-20231030153803072](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20231030153803072.png)