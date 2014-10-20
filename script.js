function update() {
	$.post( "/chat/send_update", { last_update: get_time() })
		.done(function( data ) {
			$( "#messages" ).append( data );
			$( ".scrollbar-chrome" ).scrollTop( 999999 );
	});
}

function get_time() {
	var currentTime = new Date()
	var hours = currentTime.getHours()
	var minutes = currentTime.getMinutes()
	var seconds = currentTime.getSeconds()
	if (minutes < 10){
	minutes = "0" + minutes
	}
	if (seconds < 10){
	seconds = "0" + seconds
	}
	return hours + ":" + minutes + ":" + seconds
}

$(function() {
    jQuery('.scrollbar-chrome').scrollbar();
    $( ".scrollbar-chrome" ).scrollTop( 999999 );
    
    function send_message() {
		var mess = $("input[name='message']").val();
		$.post( "/chat/send_post", { message: mess })
			.done(function( data ) {
				$( "#messages" ).append( data );
				$( ".scrollbar-chrome" ).scrollTop( 999999 );
				
		});
		$( "#chat_input" ).val("");
	}
    
    
    $( "#submit_form" ).click(function() {
		send_message();
	});
    
	$( "#chat_input" ).keydown(function( event ) {
		if ( event.which == 13 ) {
			send_message();
		}
	});	
	
	$( "#next_wall_messages" ).click(function() {
		var type_page = document.URL.split("/")[3];
		var address = "/moje-zed/next_messages";
		if (type_page == "verejna-zed") {
			address = "/verejna-zed/next_messages"
		}
		
		var num_page = parseInt($(this).attr("data-page"));
		$.post( address, { page:num_page })
			.done(function( data ) {
				$( "#messages" ).append( data );
			});
		$(this).attr("data-page", ++num_page);
	});
	
	$(document).on('click', ".comment_submit" , function() {
		var main_message = $(this).parent().parent();
		var message = $(this).parent().find(".comment_input").val();
		var main_message_id = main_message.attr("data-id");
		
		var type_page = document.URL.split("/")[3];
		var address = "/moje-zed/send_comment";
		if (type_page == "verejna-zed") {
			address = "/verejna-zed/send_comment"
		}
		
		$.post( address, { comment_message: message, message_id: main_message_id })
			.done(function( data ) {
				main_message.find(".comments").append( data );
				
		});
		$(this).parent().find(".comment_input").val("");
		
	});

	$(document).on('click', ".response" , function() {
		var comment_form = $(this).parent().find(".comment_form");
		if( $(this).html() == "Okomentovat" ){
			$(this).html("Nekomentovat");
			comment_form.css("display","block");
		}
		else
		{
			$(this).html("Okomentovat");
			comment_form.css("display","none");
		}
	})

	$(document).on('click', ".show_comments" , function() {
		 var main_message = $(this).parent();
			var main_message_id = main_message.attr("data-id");
			
			var type_page = document.URL.split("/")[3];
			var address = "/moje-zed/show_comments";
			if (type_page == "verejna-zed") {
				address = "/verejna-zed/show_comments"
			}
			var label = $(this).html().split(" ");
			var count = label[2];
			if(label[0]=="Skrýt"){
				$(this).html("Zobrazit komentáře "+count);
				main_message.find(".comment").remove();
				$(this).parent().find(".response").html("Okomentovat");
				$(this).parent().find(".comment_form").css("display","none");
			}
			else
			{
				$(this).html("Skrýt komentáře "+count)
				$.post( address, { message_id: main_message_id })
					.done(function( data ) {
						main_message.find(".comments").append( data );
						
				});
				$(this).parent().find(".response").html("Nekomentovat");
				$(this).parent().find(".comment_form").css("display","block");
			}
		});

});
