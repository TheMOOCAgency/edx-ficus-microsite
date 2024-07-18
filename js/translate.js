setInterval(function(){
  $(".problem-progress").each(function() {
    $(this).html($(this).html().replace("(ungraded)",""));
  });
  if(window.location.href.indexOf('/courseware/')>-1){
    $(".problem-progress").each(function() {
      $(this).html($(this).html().replace("(ungraded)",""));
      $(this).html($(this).html().replace("notés","noté"));
    });
    $(".poll-voting-thanks span").each(function() {
      $(this).html($(this).html().replace("Thank you","Merci"));
    });
    $(".title1").each(function() {
      $(this).html($(this).html().replace("Feedback","Commentaire"));
      $(this).html($(this).html().replace("Problem",""));
    });
    $(".unbutton.btn-default.btn-small.keyboard-help-button").each(function() {
      $(this).css("display","none");
    });
    $(".unbutton.btn-link.keyboard-help-button").each(function() {
      $(this).css("display","none");
    });
    $(".view-results-button").each(function() {
       $(this).html($(this).html().replace("View results","Voir les r&eacute;sultats"));
    });
    $(".poll-header").each(function() {
       $(this).html($(this).html().replace("Results","R&eacute;sultats"));
    });
    $(".poll-footnote").each(function() {
       $(this).html($(this).html().replace("Results gathered from ","R&eacute;sultats sur un total de "));
       $(this).html($(this).html().replace("respondent","r&eacute;pondant"));
    });
    $("h3.poll-header").each(function() {
      $(this).html($(this).html().replace("Feedback","Commentaire"));
    });
    $("input.input-main").each(function() {
       $(this).attr("value",$(this).attr("value").replace("Submit","Soumettre"));
    });
    $(".message__content").each(function() {
       $(this).html($(this).html().replace("Your Response"," Votre r&eacute;ponse"));
    });
    $("p.message").each(function() {
       $(this).html($(this).html().replace("Drag the items onto the image above.","D&eacute;posez les items sur l'image"));
    });
    $(".action.action--save.submission__save").each(function() {
       $(this).html($(this).html().replace("Save your progress","Sauvegarder votre progression"));
    });
    $("h2.bookmarks-results-header").each(function() {
       $(this).html($(this).html().replace("My Bookmarks","Mes favoris"));
    });
    $(".unbutton.btn-default.btn-small.reset-button").each(function() {
       $(this).html($(this).html().replace("Reset","Réinitialiser"));
    });
  }
  if(window.location.href.indexOf('/forum')>-1){
    $(".field-help").each(function() {
      $(this).html($(this).html().replace("Add your post to a relevant topic to help others find it.","Ajoutez votre message sur le bon sujet pour aider les autres à le trouver"));
      $(this).html($(this).html().replace("Questions raise issues that need answers. Discussions share ideas and start conversations.","Utilisez les 'Questions' si vous attendez une réponse. Les 'Discussions' servent à lancer des conversations."));
      $(this).html($(this).html().replace("Add a clear and descriptive title to encourage participation.","Ajoutez un titre clair et descriptif pour favoriser la participation"));
    });
    $("#new-post-editor-description").each(function() {
      $(this).html($(this).html().replace("Your question or idea","Votre question ou idée"));
    });
    $(".posted-details").each(function() {
      $(this).html($(this).html().replace("discussion posted ","posté"));
      $(this).html($(this).html().replace(" by "," par "));
    });
    $(".user-roles").each(function() {
      $(this).css('display','none');
    });
  }
},500);
