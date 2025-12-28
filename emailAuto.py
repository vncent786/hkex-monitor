import os
import yagmail

sender ='ragna786@gmail.com'
receiver = 'sasoye1248@badfist.com'


subject = "test"

contents = """
Hi here is the meail tests

"""

yag = yagmail.SMTP(user=sender, password=os.environ.get('python_pass'))
yag.send(to=receiver, subject=subject, contents=contents)
print('email sent!')

