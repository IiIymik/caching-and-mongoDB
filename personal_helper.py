from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit import prompt
import re
import os.path
from datetime import datetime, timedelta
from models import Contact, Email, Birthday, Phone
import connect


# --------------------------------Prompt Toolkit-------------------------------

SqlCompleter = WordCompleter([
    'add', 'close', 'exit', 'remove', 'show', 'add address', 'add birthday', 'add email', 'add phone',
    'delete address', 'delete birthday', 'delete email', 'delete phone',
    'change email', 'change birthday', 'change address', 'change phone',
    'coming birthday', 'good bye', "help", 'show all', 'search'], ignore_case=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})
# --------------------------------Prompt Toolkit-------------------------------


class CustomException(Exception):
    def __init__(self, text):
        self.txt = text


def input_error(func):
    
    def inner(command_line):
        result = None
        try:
            result = func(command_line)

        except CustomException as warning_text:
            result = warning_text

        except Exception as exc:

            if func.__name__ == 'save_func':
                result = f'Error while saving.'
            elif func.__name__ == 'add_birthday':
                result = "Day out of range for this month."
            elif func.__name__ == 'coming_birthday' and exc.__class__.__name__ == "ValueError":
                result = "Use a number for getting list of birthdays more than next 7 days."
            elif func.__name__ == 'remove':
                result = f'Error while removing record.'
            elif func.__name__ == 'change_address':
                result = f'Error while changing address.'
            elif func.__name__ == 'change_birthday':
                result = f'Error while changing birthday.'
            elif func.__name__ == 'change_email':
                result = f'Error while changing email.'
            elif func.__name__ == 'change_phone':
                result = f'Error while changing phone. Maybe you try to set phone number existing for some other contact.'
            elif func.__name__ == 'delete_address':
                result = f'Error while deleting address.'
            elif func.__name__ == 'delete_birthday':
                result = f'Error while deleting birthday.'
            elif func.__name__ == 'delete_email':
                result = f'Error while deleting email.'
            elif func.__name__ == 'delete_phone':
                result = f'Error while deleting phone.'
            elif func.__name__ == 'search':
                result = f'Error while searching.'
            elif func.__name__ == 'clean_func':
                result = f'Error while cleaning the folder.'

        return result

    return inner


@input_error
def exit_func(command_line):

    return 'Good bye!'


def prepare_value(command_line):
    if command_line:
        value = command_line.pop(-1)
        key = ' '.join(command_line)
        return key, value
    else:
        raise CustomException(
            'The command must be with INFORMATION you want to add or change (Format: <command> <ID> <information>).')


def prepare_value_3(command_line):
    if command_line:
        key = command_line[0]
        value = input('Enter the address >>> ')
        return key, value
    else:
        raise CustomException(
            'The command must be in the format: <command> <ID>.')


@input_error
def add_name(command_line):
    if command_line:
        new_name = ' '.join(command_line)
        Contact(name=new_name, address='', email=Email(),
                birthday=Birthday(), phones=[]).save()
        return f'Contact with the name "{new_name}" has been successfully added. ID = {Contact.objects().order_by("-id").first().id}'
    else:
        raise CustomException(
            'The command must be with a NAME you want to add (Format: <add> <name>).')


def check_id(command_line):

    if len(command_line) == 0:
        return 1, 'Specify ID of the contact.'

    if not command_line[0].isnumeric():
        return 2, 'Specify ID of the contact as an INTEGER number.'

    if Contact.objects(id=command_line[0]).count() == 0:
        return 3, f'There is no contact with ID = {command_line[0]}'
    else:
        return 0, ''


@ input_error
def add_address(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        key, address = prepare_value_3(command_line)
        Contact.objects(id=key).update_one(address=address)
        return f'Address "{address}" for the contact "{Contact.objects(id=key).first().name}" with ID = {key} has been successfully set.'
    else:
        return check_id_message


@ input_error
def add_birthday(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        key, birthday = prepare_value(command_line)
        if re.search('\d{2}\.\d{2}.\d{4}', birthday) and datetime.strptime(birthday, '%d.%m.%Y'):
            new_birthday = Birthday()
            new_birthday.value = birthday
            Contact.objects(id=key).update_one(birthday=new_birthday)
            return f'Birthday {birthday} for the contact "{Contact.objects(id=key).first().name}" with ID = {key} has been successfully set.'
        else:
            raise CustomException(
                'Wrong date format! Correct format is DD.MM.YYYY')
    else:
        return check_id_message


@ input_error
def add_email(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        key, email = prepare_value(command_line)
        if re.search('[a-zA-Z][\w.]+@[a-zA-z]+\.[a-zA-Z]{2,}', email):
            new_email = Email()
            new_email.value = email
            Contact.objects(id=key).update_one(email=new_email)
            return f'Email {email} for the contact "{Contact.objects(id=key).first().name}" with ID = {key} has been successfully set.'
        else:
            raise CustomException(
                'Wrong email format! Correct format is aaaa@ddd.cc')
    else:
        return check_id_message


@ input_error
def add_phone(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        key, phone = prepare_value(command_line)
        contact_to_update = Contact.objects(id=key).get()
        if len(contact_to_update.phones) == 3:
            return 'There are 3 numbers in the list of phones alredy. It cannot contain more.'
        if re.search('\(0\d{2}\)\d{3}-\d{2}-\d{2}', phone) and len(phone) == 14:
            if phone in create_phones_list(contact_to_update.phones):
                return f'Phone number {phone} is already present for the contact "{contact_to_update.name}" with ID = {key}'
            else:
                new_phone = Phone()
                new_phone.value = phone
                contact_to_update.phones.append(new_phone)
                contact_to_update.save()
                return f'Phone {phone} for the contact "{contact_to_update.name}" with ID = {key} has been successfully added.'
        else:
            raise CustomException(
                'Wrong phone number format! Use (0XX)XXX-XX-XX format!')
    else:
        return check_id_message


@ input_error
def coming_birthday(command_line):

    if command_line:
        range_days = int(command_line[0])
    else:
        range_days = 7

    contacts_count = 0
    for contact in Contact.objects.all():
        if contact.birthday.value:
            current_date = datetime.now().date()
            timedelta_filter = timedelta(days=range_days)
            birthday_date = datetime.strptime(
                contact.birthday.value, '%d.%m.%Y').date()
            current_birthday = birthday_date.replace(year=current_date.year)
            if current_date <= current_birthday <= current_date + timedelta_filter:
                print_contact(contact)
                contacts_count += 1
    if contacts_count == 0:
        return f'There are no birthdays coming within this period.'
    else:
        return f'Number of contacts found: {contacts_count}'


@ input_error
def remove(command_line):

    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        contact_to_remove = Contact.objects(id=command_line[0]).get().name
        Contact.objects(id=command_line[0]).delete()
        return f'Contact "{contact_to_remove}" with ID = {command_line[0]} has been successfully removed.'
    else:
        return check_id_message


def clear_field(command_line, field_name, field_lable):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        if field_name == 'address':
            Contact.objects(id=command_line[0]).update_one(address='')
        if field_name == 'email':
            new_email = Email()
            new_email.value = ''
            Contact.objects(id=command_line[0]).update_one(email=new_email)
        if field_name == 'birthday':
            new_birthday = Birthday()
            new_birthday.value = ''
            Contact.objects(id=command_line[0]).update_one(
                birthday=new_birthday)
        return f'{field_lable} for the contact "{Contact.objects(id=command_line[0]).get().name}" with ID = {command_line[0]} has been successfully deleted.'
    else:
        return check_id_message


@ input_error
def delete_address(command_line):
    return clear_field(command_line, 'address', 'Address')


@ input_error
def delete_birthday(command_line):
    return clear_field(command_line, 'birthday', 'Date of birth')


@ input_error
def delete_email(command_line):
    return clear_field(command_line, 'email', 'Email')


@ input_error
def delete_phone(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        key, phone = prepare_value(command_line)
        contact_to_update = Contact.objects(id=key).get()
        if phone in create_phones_list(contact_to_update.phones):
            for i in range(len(contact_to_update.phones)):
                if contact_to_update.phones[i].value == phone:
                    contact_to_update.phones.pop(i)
                    break
            contact_to_update.save()
            return f'Phone number {phone} for the contact "{contact_to_update.name}" with ID = {command_line[0]} has been successfully deleted.'
        else:
            return f'The phone number {phone} is not found for this contact!'
    else:
        return check_id_message


@ input_error
def change_address(command_line):
    return add_address(command_line)


@ input_error
def change_birthday(command_line):
    return add_birthday(command_line)


@ input_error
def change_email(command_line):
    return add_email(command_line)


@ input_error
def change_phone(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        if len(command_line) != 3:
            raise CustomException(
                'The command must be with an ID and 2 phones you want to change\n(Format: <change phone> <ID> <old phone> <new phone>)')
        phones = [command_line.pop(-1)]
        phones.insert(0, command_line.pop(-1))
        if re.search('\(0\d{2}\)\d{3}-\d{2}-\d{2}', phones[0]) and re.search('\(0\d{2}\)\d{3}-\d{2}-\d{2}', phones[1]) and \
           len(phones[0]) == 14 and len(phones[1]) == 14:
            contact_to_update = Contact.objects(id=command_line[0]).get()
            if phones[1] in create_phones_list(contact_to_update.phones):
                raise CustomException(
                    f'The phone number {phones[1]} is already present in the list of phones.')
            if phones[0] in create_phones_list(contact_to_update.phones):
                for i in range(len(contact_to_update.phones)):
                    if contact_to_update.phones[i].value == phones[0]:
                        contact_to_update.phones[i].value = phones[1]
                        break
                contact_to_update.save()
                return f'Phone {phones[0]} for the contact "{contact_to_update.name}" with ID = {command_line[0]} has been successfully changed for {phones[1]}.'
            else:
                return f'The phone number {phones[0]} is not found for this contact!'
        else:
            raise CustomException(
                'Wrong phone number format! Use (0XX)XXX-XX-XX format!')
    else:
        return check_id_message


@ input_error
def help_common(command_line):

    try:
        file = open(
            f"{os.path.dirname(os.path.abspath(__file__))}/help.txt", 'r')
        help_lines = file.readlines()
        for i in help_lines:
            print(i[:len(i)-1])
        file.close()
        msg = "The end of the help."
    except:
        msg = "File help.txt is not found."
    return msg


def create_phones_list(phones):
    if phones == []:
        return '---'
    else:
        phones_list = [phone.value for phone in phones]
        return ', '.join(phones_list)


def print_contact(contact):

    address = '---' if contact.address == '' else contact.address
    email = '---' if contact.email.value == '' else contact.email.value
    birthday = '---' if contact.birthday.value == '' else contact.birthday.value

    print(f'\nID {contact.id} {"-" * (105 - len(str(contact.id)))}┐\
            \n| {contact.name:<51} Phones: {create_phones_list(contact.phones):<46} |\
            \n| Email: {email:<73} Date of birth: {birthday:<10} |\
            \n| Address: {address:<97} |\n└{"-" * 108}┘')


@ input_error
def search(command_line):
    if command_line:
        search_str = ' '.join(command_line).strip()
        contacts_count = 0
        for contact in Contact.objects.all():
            if search_str.lower() in contact.name.lower() or \
               search_str.lower() in contact.address.lower() or \
               search_str.lower() in create_phones_list(contact.phones) or \
               search_str.lower() in contact.email.value.lower() or \
               search_str.lower() in contact.birthday.value.lower():
                print_contact(contact)
                contacts_count += 1
        if contacts_count == 0:
            return f'There are no contacts matching the search string "{search_str}" in the book.'
        else:
            return f'Number of contacts found: {contacts_count}'
    else:
        return 'Specify the search string.'


@ input_error
def show_all(command_line):
    contacts_count = Contact.objects.count()
    if contacts_count > 0:
        for contact in Contact.objects.all():
            print_contact(contact)
        return f'Number of contacts: {contacts_count}'
    else:
        return 'There are no contacts in the book.'


@ input_error
def show_id(command_line):
    check_id_result, check_id_message = check_id(command_line)
    if check_id_result == 0:
        for contact in Contact.objects(id=command_line[0]):
            print_contact(contact)
        return ''
    else:
        return check_id_message


COMMANDS = {
    'close': exit_func,
    'exit': exit_func,
    'good bye': exit_func,
    'add': add_name,
    'add address': add_address,
    'add birthday': add_birthday,
    'add email': add_email,
    'add phone': add_phone,
    'remove': remove,
    'delete address': delete_address,
    'delete birthday': delete_birthday,
    'delete email': delete_email,
    'delete phone': delete_phone,
    'change email': change_email,
    'change birthday': change_birthday,
    'change address': change_address,
    'change phone': change_phone,
    'coming birthday': coming_birthday,
    "help": help_common,
    'show': show_id,
    'show all': show_all,
    'search': search
}

ONE_WORD_COMMANDS = ['add', 'close', 'help',
                     'exit', 'remove', 'search', 'show']
TWO_WORDS_COMMANDS = ['add address', 'add birthday', 'add email', 'add phone',
                      'delete address', 'delete birthday', 'delete email', 'delete phone',
                      'change email', 'change birthday', 'change address', 'change phone',
                      'coming birthday', 'good bye', 'show all']


def get_handler(command):
    return COMMANDS[command]


def main():

    print(
        f'Database "Contacts" is connected. It has {Contact.objects.count()} contacts.')
    print("Enter 'help' command to see all the commands available.")

    while True:
        command_line = []
        while not command_line:
            command_line = prompt('>>> ',
                                  history=FileHistory('history'),
                                  auto_suggest=AutoSuggestFromHistory(),
                                  completer=SqlCompleter,
                                  style=style
                                  ).split()

        right_command = False

        if len(command_line) > 1 and \
           f'{command_line[0].lower()} {command_line[1].lower()}' in TWO_WORDS_COMMANDS:
            command = f'{command_line.pop(0).lower()} {command_line.pop(0).lower()}'
            right_command = True

        if not right_command:
            command = command_line.pop(0).lower()
            right_command = command in ONE_WORD_COMMANDS

        if not right_command:
            print(
                f'The "{command}" command is wrong! The allowable commands are {", ".join(ONE_WORD_COMMANDS + TWO_WORDS_COMMANDS)}.')
            continue

        handler = get_handler(command)
        print(handler(command_line))
        if handler is exit_func:
            break


if __name__ == '__main__':
    main()