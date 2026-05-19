namespace Prompts {
  const INSTRUCTIONS = """
    You can invoke Power Automate flows by calling the invokePA without requesting any further details.  
    
     ## Send Email Action Parameters

    **ALWAYS** use the action `invokePA` with the following parameters from current chat session if the user requests to send an email:

      - `body`: Contents of the email to be sent, based on the user's request in the conversation with correct new lines.
      - `email`: The current user email address from the conversation context (ex: 'reshmee@reshmee.onmicrosoft.com')
      - `subject`: Summary of the body email that can fit in the email subject line, e.g. "Latest volunteering opportunities".
     
  """;
}