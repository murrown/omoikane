const selectionform = $("#selectionform")[0];
const quizform = $("#quizform")[0];
const resultsdiv = $("#results")[0];
const answerfield: HTMLInputElement = <HTMLInputElement>$("#answerfield")[0];
const answeryesno = $("#answeryesno")[0];
const answertext = $("#answertext")[0];
const continuediv = $("#continue")[0];
const audiobtn = $("#audiobtn")[0];
const static_url = $("#static")[0].innerHTML;

class Association {
    constructor(public expression: string, public reading: string, public sense: string){}

    toString(): string{
        if (this.reading == null){
            return this.sense;
        }
        return ("<tr><td class=\"p-1 align-top\">" + this.reading
                + ":</td><td class=\"p-1 align-top\" style=\"max-width: 18rem;\">"
                + this.sense + "</td></tr>");
    }
}

class Question {
    public associations: Association[] = [];

    constructor(public expression: string, public readings: string[],
                assoc_list: any[], public audio: string){
        for (var val of assoc_list) {
            let association = new Association(expression, val.reading, val.sense);
            this.associations.push(association);
        }
    }

    expression_with_breaks(): string{
        var broken: string[] = this.expression.split(" ");
        if (broken.length <= 1){
            return this.expression;
        }
        var spanstyle: string =  "<span style=\"display:inline-block\">"
        return spanstyle + broken.join("</span> " + spanstyle) + "</span>"
    }

    toString(): string{
        var s: string = "";
        if (this.readings.length >= 1){
            s += "<small>" + this.readings.join(", ") + "</small><br>"
        }
        return (s + "<table>" + this.associations.join("") + "</table>");
    }
}

class QuizList {
    constructor(public name: string, public id: number){}
}

class Quiz {
    public questions: Question[] = [];
    public quizlist: QuizList | null = null;
    public active_question: Question | null = null;

    constructor(){}

    get_next_question(){
        if (this.active_question == null && this.questions.length > 0){
            this.active_question = this.questions.shift()!;
            continuediv.style.display = "none";
            $("#expression_text").html(this.active_question.expression_with_breaks());
            $("#expression_text")[0].style.display = "block";
            if (this.active_question.readings.length > 0){
                answeryesno.style.display = "none";
                answertext.style.display = "block";
                answerfield.focus();
            } else {
                answertext.style.display = "none";
                answeryesno.style.display = "block";
                $("#answeryesbtn")[0].focus();
            }
            if (this.active_question.audio) {
                audiobtn.style.display = "block";
            } else {
                audiobtn.style.display = "none";
            }
        }
    }

    finish(){
        continuediv.style.display = "none";
        answeryesno.style.display = "none";
        answertext.style.display = "none";
        $("#expression_text").html("All done!");
    }

    show_question(){
        const thisquiz: Quiz = this;
        if (this.quizlist==null || this.quizlist.id==null){
            return;
        }
        this.active_question = null;
        audiobtn.style.display = "none";
        resultsdiv.style.display = "none";
        $("#expression_text")[0].style.display = "none";
        continuediv.style.display = "none";
        answerfield.value = "";
        if (thisquiz.questions.length == 0){
            $.post("/quiz/post/due", {"quizlist": this.quizlist.id},
                  function(response){
                for (var val of response.results) {
                    let q = new Question(val.expression, val.readings, val.associations, val.audio);
                    thisquiz.questions.push(q);
                }
                if (thisquiz.questions.length == 0){
                    thisquiz.finish();
                } else {
                    thisquiz.get_next_question();
                }
            })
        } else {
            thisquiz.get_next_question();
        }
    }

    select_list(quizlist: QuizList){
        if (this.quizlist != quizlist){
            this.quizlist = quizlist;
        }
        this.show_question();
        selectionform.style.display = "none";
        quizform.style.display = "block";
        $("#quizlist_title").html(this.quizlist.name);
    }

    initialize_selection(){
        const thisquiz: Quiz = this;
        $.get("/quiz/get/lists", function(response){
            var did_focus: boolean = false;
            for (var val of response.results) {
                let row = $("<tr>");
                let scorecell = $("<td class=\"p-3\">");
                let namecell = $("<td>");
                let quizlist = new QuizList(val.name, val.id);
                let link = $("<button class=\"btn btn-primary\">");
                scorecell.html(val.done + " / " + val.tried + " / " + val.total);
                row.append(scorecell);
                row.append(namecell);
                link.html(val.name);
                namecell.append(link);
                link.click(function(e){
                    e.preventDefault();
                    thisquiz.select_list(quizlist);
                })
                $("#selectiontable").append(row);
                if (did_focus == false) link.focus();
            }
            quizform.style.display = "none";
            selectionform.style.display = "block";
        })
    }

    show_results(){
        if (this.active_question == null){
            return;
        }
        answertext.style.display = "none";
        answeryesno.style.display = "none";
        continuediv.style.display = "block";
        $("#continuebtn")[0].focus();
        resultsdiv.style.display = "block";
        resultsdiv.innerHTML = this.active_question.toString();
    }

    guess(success: boolean|null = null){
        const thisquiz: Quiz = this;
        var success_url: string;
        var answer: string;
        if (this.active_question == null){
            return;
        }
        if (success == null){
            success = false;
            answer = answerfield.value;
            if (!answer){
                return;
            }
            for (var reading of this.active_question.readings){
                if (answer == reading){
                    success = true;
                    break;
                }
            }
        }
        if (success == true){
            success_url = "/quiz/post/success";
            $("#results").removeClass("bg-danger").addClass("bg-success");
        } else {
            success_url = "/quiz/post/failure";
            $("#results").removeClass("bg-success").addClass("bg-danger");
        }
        $.post(success_url, {"expression": this.active_question.expression},
               function(response){
            answerfield.value = "";
            thisquiz.show_results();
        })
    }

    submit() {
        if ($("#continue")[0].style.display != "none"){
        }
    }
}

const quiz = new Quiz();

$(document).ready(function(){
    quiz.initialize_selection();
    $(document).keypress(function(e) {
        if (e.key == "Enter" && answertext.style.display != "none"){
            e.preventDefault();
            quiz.guess();
        } else if ((e.key == "Enter" || e.key == "c") && continuediv.style.display != "none"){
            e.preventDefault();
            $("#continuebtn").trigger("click");
        } else if (e.key == "p" && audiobtn.style.display != "none"){
            e.preventDefault();
            $("#audiobtn").trigger("click");
        } else if (answeryesno.style.display != "none"){
            if (e.key == "y"){
                e.preventDefault();
                $("#answeryesbtn").trigger("click");
            } else if (e.key == "n"){
                e.preventDefault();
                $("#answernobtn").trigger("click");
            }
        }
    })
    $("#continuebtn").click(function(e){
        e.preventDefault();
        quiz.show_question();
    })
    $("#answeryesbtn").click(function(e){
        e.preventDefault();
        quiz.guess(true);
    })
    $("#answernobtn").click(function(e){
        e.preventDefault();
        quiz.guess(false);
    })
    $("#audiobtn").click(function(e){
        e.preventDefault();
        if (quiz.active_question != null && quiz.active_question.audio){
            new Audio(static_url + quiz.active_question.audio).play();
        }
    })
});
