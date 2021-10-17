import PySimpleGUI as sg
from PIL import Image
from io import BytesIO
from cryptImg import cryptImg
from gallery import gallery_ico
ci = cryptImg()

sg.theme('DarkAmber')
sg.set_options(font=('Roboto', 10))

FILE_TYPES = (
    ("jpeg", "*.jpeg"),
    ("jpg", "*.jpg"),
    ("png", "*.png")
)


def get_img(content: bytes, maxsize=(400, 400)):
    bytes_img = BytesIO()
    img = Image.open(BytesIO(content))
    img.thumbnail(maxsize)
    img.save(bytes_img, format='PNG')
    return bytes_img.getvalue()



# -----------------------left column

lcol = [
    [
        sg.Input(size=(10, 1), enable_events=True, key='_INPATH_', expand_x=True, expand_y=True, background_color='grey7'),

        sg.FileBrowse(button_text='Open', file_types=FILE_TYPES, size=(4, 1), tooltip='Open Image', target='_INPATH_'),
        
        sg.Button('Read', key='_READ_', enable_events=True, disabled=True, size=(4, 1)),

        sg.Button('x', enable_events=True, disabled=True, size=(1, 1), key='_CLOSE_', tooltip='Close Image')
    ],

    [sg.Image(background_color='black', key='_IMAGE_', size=(400, 400), data=gallery_ico,)]
]




left_col = sg.Column(lcol, justification='left', key='_IMCOL_', element_justification='center', expand_x=True, expand_y=True, size=(400, 500), pad=(5, 20))




# ----------------------right column

rcol = [
    [sg.Text('Message'),],

    [sg.Text(text='', enable_events=True, size=(100, 6), pad=(5, 10), background_color='black', expand_y=True, key='_MESSAGE_')],

    [
        sg.Button('Clear', size=(5, 1), key='_CLEARM_', disabled=True, enable_events=True),
        sg.Button('Delete', size=(6, 1), disabled=True, enable_events=True, key='_DEL_'),
    ],

    [sg.Text('Write your message: ', pad=((5, 0), (15, 5)))],

    [sg.Multiline(default_text='', size=(100, 8), enable_events=True, background_color='grey12', pad=((5, 5), (0, 10)), expand_x=True, key='_WMSG_')],

    [
        sg.Button('Write', size=(5, 1), key='_APPEND_', disabled=True, enable_events=True),
        sg.Text('Successful!', key='_SUCCESSMSG_', visible=False, text_color='white', font=('Roboto', 8))
    ],
]




right_col = sg.Column(layout=rcol, size=(400, 500), justification='right', key='_TXTCOL_', element_justification='left', expand_x=True, expand_y=True, pad=(5, 20))




# --------------------final layout-----------------------------------------


layout = [
    [left_col, right_col],
]




#----------------------------password window layout--------------------------------


def initiate_password_window():
    pass_layout = [
        [
            sg.Text('Password', justification='left', expand_x=True),
            sg.Text('Incorrect Password', key='_INCPASSMSG_', font=('Roboto', 8), text_color='white', enable_events=True, visible=False, expand_x=True)
        ],

        [sg.Input(size=(20, 1), focus=True, password_char='*', key='_PASSWORD_', enable_events=True, expand_x=True)],

        [
            sg.Button('Submit', key='_SUBMIT_', bind_return_key=True),
            sg.Button('Cancel', key='_CANCEL_')
        ]
    ]

    pass_win = sg.Window('Password', layout=pass_layout, keep_on_top=True, size=(250, 150), element_padding=(10, 10))

    return pass_win




# --------------------Main--------------------------------

def main():
    win = sg.Window(title='Image', layout=layout, finalize=True, size=(1000, 500))
    fp = None

    write = False

    while True:
        event, values = win.read()
        if event == 'Exit' or event == sg.WIN_CLOSED:
            break

        #---------------------update success msg----------------------------


        if write:
            win['_SUCCESSMSG_'].Update(visible=False)
            write = False



        #-----------------------------open image--------------------------------



        if event == '_INPATH_':
            # close current file if open
            if fp is not None:
                fp.close()

            # read file
            filename = values['_INPATH_']
            fp = open(filename, 'rb+')
            content = fp.read()

            # update image
            win['_IMAGE_'].Update(size=(400, 400), data=get_img(content))
            
            # update button
            win['_APPEND_'].Update(disabled=False)
            win['_READ_'].Update(disabled=False)
            win['_CLOSE_'].Update(disabled=False)




        #---------------------read message----------------------------



        if event == '_READ_':

            password = ''

            #create password window
            pass_win = initiate_password_window()

            incorrect_pass = False
            no_msg = False

            # open password window
            while True:
                pass_event, pass_values = pass_win.read()

                if incorrect_pass:
                    pass_win['_INCPASSMSG_'].Update(visible=False)
                    incorrect_pass = False

                if pass_event == '_CANCEL_' or pass_event == 'Exit' or pass_event == sg.WIN_CLOSED:
                    break

                if pass_event == '_SUBMIT_':
                    password = pass_values['_PASSWORD_']

                    #decode msg
                    decoded_msg, status = ci.getMessage(fp=fp, content=content, password=password, delete_on_read=False)

                    # check status of password (-1 -> wrong, 0 -> correct)
                    if status == -1:
                        pass_win['_INCPASSMSG_'].Update(visible=True)
                        pass_win['_PASSWORD_'].Update(value='')
                        incorrect_pass = True
                    
                    elif status == 1:
                        no_msg = True
                        break

                    else:
                        if decoded_msg:
                            # update message
                            win['_MESSAGE_'].Update(value=decoded_msg)
                            
                            # update buttons
                            win['_CLEARM_'].Update(disabled=False)
                            win['_DEL_'].Update(disabled=False)

                        break

            pass_win.close()
                
            # pop up if no message encoded
            if no_msg:
                sg.Popup('No message found !', auto_close=True, auto_close_duration=4, title='', keep_on_top=True)



        #------------------------clear or delete read----------------------



        if event == '_CLEARM_' or event == '_DEL_':
            win['_MESSAGE_'].Update(value='')

            if event == '_DEL_':
                ci.delMsg(fp=fp, content=content)

            win['_CLEARM_'].Update(disabled=True)
            win['_DEL_'].Update(disabled=True)




        #--------------------write message-------------------------------



        if event == '_APPEND_':
            # create password window
            pass_win = initiate_password_window()
            
            write_pass = ''

            # open window
            while True:
                pass_event, pass_values = pass_win.read()

                if pass_event == '_CANCEL_' or pass_event == 'Exit' or pass_event == sg.WIN_CLOSED:
                    break

                if pass_event == '_SUBMIT_':
                    write_pass = pass_values['_PASSWORD_']
                    break

            pass_win.close()


            ci.embedMsg(fp=fp, content=content, message=values['_WMSG_'], password=write_pass)

            write = True
            win['_SUCCESSMSG_'].Update(visible=True)

            # clear
            win['_WMSG_'].Update(value='')




        #----------------------close image------------------------------------



        if event == '_CLOSE_':
            fp.close()
            del content

             # update image
            win['_IMAGE_'].Update(size=(400, 400), data=gallery_ico)

            win['_MESSAGE_'].Update(value='')

            win['_CLOSE_'].Update(disabled=True)
            win['_CLEARM_'].Update(disabled=True)
            win['_DEL_'].Update(disabled=True)
            win['_APPEND_'].Update(disabled=True)
            win['_READ_'].Update(disabled=True)



    win.close()


# ------------execute---------------------------------

if __name__ == "__main__":
    main()
