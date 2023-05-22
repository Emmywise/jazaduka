import phonenumbers


def clean_phone_number(phone_number):
    accepted_country_codes = ["KE"]
    valid = False

    for region in accepted_country_codes:
        try:
            parse_number = phonenumbers.parse(f"+{str(phone_number)}", region=region)
            if phonenumbers.is_valid_number_for_region(parse_number, region):
                valid = True
        except phonenumbers.NumberParseException:
            pass
    return valid
