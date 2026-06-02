(function(System,$){$(function(){var tab_content_item=[{label:"misspell",name:"字词错误"},{label:"senseWord",name:"敏感词"},{label:"punctuation",name:"标点符号"},{label:"grammarOrder",name:"语序语法"},{label:"knowledgeCheck",name:"知识检查"},{label:"innerDuplicate",name:"文内查重"}];var Data=System.operateState.getSuggestions(Report.report_id);var suggestions=Data.length==0?JSON.parse(suggestion_json):Data;System.operateState.saveSuggestions(Report.report_id,suggestions);var obj={suggestions:suggestions};parent.postMessage(obj,"*");var Typeof=typeof is_organization;if(Typeof=="boolean"&&is_organization==true){var add_item=[{label:"leadership",name:"领导人"},{label:"political",name:"政治导向"}];$.each(add_item,function(i,v){tab_content_item.splice(4,0,v)})}var tabs={tab:function(){var lis="";$.each(tab_content_item,function(i,item){var li=`<li data-type="${item.label}">
                                <span class="rp-${item.label}"></span>
                                <span class="label-name">${item.name}</span>
                                <span class="subscript">( 0 )</span>
                            </li>`;lis+=li});$(".tab-header-items").append(lis)},item:function(){var tab=$(".tab-header li");var tab_content=$(".item-column-wrap");var span=$(".item-title span");for(var i=0;i<tab.length;i++){new function(i){tab[i].onclick=function(){tab.removeClass("active");$(this).addClass("active");tab_content.html("");var type=$(this).data("type");$(".item-title h4").html($(this).find(".label-name").text());$(".item-title span").html(0);span.removeClass();span.addClass("rp-"+type+"");parent.postMessage({type:type},"*");System.operateState.saveProofTab(Report.report_id,type);switch(type){case"All":var suggestions=System.operateState.getSuggestions(Report.report_id);All_Tab(suggestions);break;case"ignore":var _ignore=$(this);Ignore_Tab(_ignore);break;default:Item_Tab(type,All_Tab);break}}}(i)}}};function SubScript(suggestions){var regroup=handle(suggestions);for(var i in regroup){for(var n in regroup[i]){var num=0;$.each(regroup[i][n],function(k,v){if(v.ignore==false){num++}});$(".tab-header-items li").each(function(){if($(this).data().type==n){$(this).find(".subscript").html("( "+num+" )")}})}}}function Item_Tab(type,All_Tab){var suggestions=System.operateState.getSuggestions(Report.report_id);var regroup=handle(suggestions);for(var i in regroup){for(var n in regroup[i]){if(n==type){All_Tab(regroup[i][n])}}}}function Ignore_Tab(_ignore){var suggestions=System.operateState.getSuggestions(Report.report_id);var IgnoreSuggestions=[];for(var i=0;i<suggestions.length;i++){if(suggestions[i].ignore){IgnoreSuggestions.push(suggestions[i])}}All_Tab(IgnoreSuggestions,_ignore);$(".icon_tooltip").removeClass("ignore");$(".icon_tooltip").addClass("resume");$(".item-title span").html(IgnoreSuggestions.length);$(".item-title h4").html("已忽略");$(".item-column").css("border-color","#c5c5c5")}tabs.tab();tabs.item();All_Tab(suggestions);calcHeight();SubScript(suggestions);var ignore=$(".item-column:hidden").length;$(".ignore_num").html(ignore);var ProofTab=System.operateState.getProofTab(Report.report_id);if(ProofTab==""){$(".tab-header li[data-type=All]").click()}else{$(".tab-header li[data-type="+ProofTab+"]").click()}function handle(list){const obj={};list.forEach(item=>{let{id,suggestionType,start_pos,end_pos,originText,suggestionWord,suggestionMsg,actionType,duplicateData,blankList,refData,ignore}=item;let temp={id:id,suggestionType:suggestionType,start_pos:start_pos,end_pos:end_pos,originText:originText,suggestionWord:suggestionWord,suggestionMsg:suggestionMsg,actionType:actionType,duplicateData:duplicateData,blankList:blankList,refData:refData,ignore:ignore};if(obj[suggestionType]){obj[suggestionType].push(temp)}else{obj[suggestionType]=[temp]}});return Object.values(obj).map(val=>{return{[val[0].suggestionType]:val}})}function All_Tab(suggestions,_ignore){var tooltip=`
                <div class="item-column-right">
                    <div class="icon_tooltip ignore"></div>
                </div>
            `;$.each(suggestions,function(i,val){var str="";var initPage=System.operateState.getProofInitPage(Report.report_id);var url=initPage=="proof_switch_text"?"text_proof.html":"standard_proof.html";switch(val.suggestionType){case"misspell":str=misspell(val,url);break;case"senseWord":str=senseWord(val,url);break;case"punctuation":str=punctuation(val,url);break;case"grammarOrder":str=grammarOrder(val,url);break;case"political":str=political(val,url);break;case"leadership":str=leadership(val,url);break;case"knowledgeCheck":str=knowledgeCheck(val,url);break;case"innerDuplicate":str=innerDuplicate(val,url);break}$(".item-column-wrap").append(str);if(!_ignore){if(val.ignore){$("#"+val.id+"").css("display","none")}else{$("#"+val.id+"").css("display","block")}}});var ignore=$(".item-column:hidden").length;var total=$(".item-column").length-ignore;$(".item-title span").html(total);$(".item-column").append(tooltip);calcHeight()}function misspell(element,url){if(element.suggestionWord==""){var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column misspell">
                            <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                <div class="flex-center">
                                    <div class="font">${element.originText}</div>
                                    <div class="root">建议：${element.suggestionMsg}</div>
                                </div>
                            </a>
                        </div>
                    <div>
                `}else{var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column misspell">
                            <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                <span class="font replace replace_before">${element.originText}</span>
                                <span class="root">建议替换为></span>
                                <span class="font replace replace_after copy_ctx"> ${element.suggestionWord} <span class="icon_copy"></span></span>
                            </a>
                        </div>
                    </div>
                `}return html}function senseWord(element,url){if(element.suggestionWord==""){var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column senseWord">
                            <a href="${url}#${element.id}" target="left" class="item-column-callback">
                                <div class="flex-center">
                                    <div class="font">${element.originText}</div>
                                    <b class="ML20">检测到敏感词</b>
                                </div>
                                <div class="item-column-title MT20">建议：${element.suggestionMsg}</div>
                            </a>
                        </div>
                    </div>
                `}else{var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column senseWord">
                            <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                <span class="font replace replace_before">${element.originText}</span>
                                <span class="root">建议替换为></span>
                                <span class="font replace replace_after copy_ctx"> ${element.suggestionWord} <span class="icon_copy"></span></span>
                            </a>
                        </div>
                    </div>
                `}return html}function punctuation(element,url){if(element.originText.trim()==""){var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column punctuation disabled">
                            <div class="item-column-callback">
                                ${element.blankList.map((list,i)=>`
                                    <div class="item-column-title">${i+1}、建议： ${list.suggestionMsg} </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                `}else{if(element.suggestionWord==""){var html=`
                        <div id="${element.id}" class="anchorPoint">
                            <div class="item-column punctuation">
                                <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                    <div class="flex-center">
                                        <div class="font">${element.originText}</div>
                                        <div class="root">建议：${element.suggestionMsg}</div>
                                    </div>
                                </a>
                            </div>
                        </div>
                    `}else{var html=`
                        <div id="${element.id}" class="anchorPoint">
                            <div class="item-column punctuation">
                                <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                    <span class="font replace replace_before"> ${element.originText} </span>
                                    <span class="root">建议替换为></span>
                                    <span class="font replace replace_after"> ${element.suggestionWord} </span>
                                </a>
                            </div>
                        </div>
                    `}}return html}function grammarOrder(element,url){if(element.suggestionWord==""){var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column grammarOrder">
                            <a href="${url}#${element.id}" target="left" class="item-column-callback">
                                <div class="item-column-title MB10">语序语法问题</div>
                                <div class="grammar-detail">
                                    <div>${element.originText}</div>
                                    <div class="item-column-title MT20 MB10">建议修改为></div>
                                    <div class="copy_ctx"> ${element.suggestionMsg} <span class="icon_copy"></span></div>
                                </div>
                            </a>
                        </div>
                    </div>
                `}else{var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column grammarOrder">
                            <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                <span class="font replace replace_before"> ${element.originText} </span>
                                <span class="root">建议替换为></span>
                                <span class="font replace replace_after copy_ctx"> ${element.suggestionWord} <span class="icon_copy"></span></span>
                            </a>
                        </div>
                    </div>
                `}return html}function political(element,url){var html=`
                <div id="${element.id}" class="anchorPoint">
                    <div class="item-column political">
                        <div class="item-column-callback politics-detail">
                            <a href="${url}#${element.id}" target="left">
                                <div class="item-column-title flex-between MB10">
                                    <div>政治导向</div>
                                    <div>相似度：<span class="hight-color">${element.refData.similarity*100}%</span></div>
                                </div>
                                <div><span style="color:#b0b0b0;">您的句子：</span><span class="title">${element.originText}<span></div>
                            </a>
                            <a href="${element.refData.refUrl}" target="_blank">
                                <div class="item-column-title MB10">相似原文片段:</div>
                                <div class="title">${element.refData.refText}</div>
                                <div class="source">来源：<span class="title source-link">《${element.refData.refTitle}》</span></div>
                            </a>
                        </div>
                    </div>
                </div>
            `;return html}function leadership(element,url){var html=`
                <div id="${element.id}" class="anchorPoint">
                    <div class="item-column leadership">
                        <a href="${url}#${element.id}" target="left" class="item-column-callback">
                            <div class="font">${element.originText}</div>
                            <div class="item-column-title MT20">建议：${element.suggestionMsg}</div>
                        </a>
                    </div>
                </div>
            `;return html}function knowledgeCheck(element,url){if(element.suggestionWord==""){var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column knowledgeCheck">
                            <a href="${url}#${element.id}" target="left" class="item-column-callback">
                                <div class="item-column-title MB10">知识检查问题</div>
                                <div class="font">${element.originText}</div>
                                <div class="item-column-title MT20 MB10">检查意见为></div>
                                <div class="font copy_ctx"> ${element.suggestionMsg} <span class="icon_copy"></span></div>
                            </a>
                        </div>
                    </div>
                `}else{var html=`
                    <div id="${element.id}" class="anchorPoint">
                        <div class="item-column knowledgeCheck">
                            <a href="${url}#${element.id}" target="left" class="item-column-callout">
                                <span class="font replace replace_before">${element.originText}</span>
                                <span class="root">建议替换为></span>
                                <span class="font replace replace_after copy_ctx"> ${element.suggestionWord} <span class="icon_copy"></span></span>
                            </a>
                        </div>
                    </div>
                `}return html}function innerDuplicate(element,url){var html=`
                <div id="${element.id}" class="anchorPoint">
                    <div class="item-column innerDuplicate">
                        <div class="item-column-callback">
                            <div class="item-column-title">上下文相似度过高</div>
                            <a href="${url}#${element.id}" target="left" class="inner_origin">${element.originText}</a>
                        
                            <div class="item-column-title">相似度语句</div>
                            <div class="innerDuplicate_list">
                                ${element.duplicateData.map((duplicate,i)=>`
                                    <div>
                                        <div class="similarity">${i+1}.相似度：<span class="hight-color">${duplicate.similarity*100}%</span></div>
                                        <a href="${url}#${duplicate.id}" id="${duplicate.id}" target="left">${duplicate.similarText}</a>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                </div>
            `;return html}function calcHeight(){let $HeaderHeight=$(".tab-header").height();$(".tab-content").css("padding-top",$HeaderHeight+40);var $LastHeight=$(".item-column:last").height();var $ContentHeight=$(".tab-content").height()-35;$(".AddHeight").height($ContentHeight-$LastHeight)}function toast(msg){let toast=`<div class="toast"><div class="toast-body">${msg}</div></div>`;$("body").append(toast);setTimeout(()=>{$(".toast").remove()},1e3)}$(document).on("click",".icon_copy",function(){var text=$(this).parents(".anchorPoint").find(".copy_ctx").text();var copyVal=$("#copyVal");copyVal.val(text);copyVal.select();document.execCommand("copy");toast("复制成功");return false});$(document).delegate(".item-column-right .icon_tooltip","mouseenter",function(){var top=$(this).offset().top;var ProofTab=System.operateState.getProofTab(Report.report_id);$(".proof-wrap").append('<div class="btn-tooltip tooltip"></div>');if(ProofTab=="ignore"){$(".btn-tooltip.tooltip").html("恢复")}else{$(".btn-tooltip.tooltip").html("忽略")}$(".btn-tooltip").css("top",top-40)});$(document).delegate(".item-column-right .icon_tooltip","mouseout",function(){$(".proof-wrap .btn-tooltip").remove()});$(document).on("click",".tabs li",function(){$(".proof-wrap .tab-content-item").scrollTop(0)});$(document).on("click",".item-column-right .icon_tooltip",function(){var id=$(this).parents(".anchorPoint").attr("id");var suggestions=System.operateState.getSuggestions(Report.report_id);for(var i=0;i<suggestions.length;i++){if(suggestions[i].id==id){if($(this).hasClass("ignore")){suggestions[i].ignore=true;$(".ignore_num").html($(".ignore_num").html()-0+1)}else{suggestions[i].ignore=false;$(".ignore_num").html($(".ignore_num").html()-0-1)}}}var obj={suggestions:suggestions};parent.postMessage(obj,"*");System.operateState.saveSuggestions(Report.report_id,suggestions);SubScript(suggestions);$(this).parents(".anchorPoint").css("display","none");$(".item-title span").html($(".item-title span").html()-0-1);var obj={IgnoreResumId:id};parent.postMessage(obj,"*")});$(document).on("click",".item-column a",function(){$(".item-column").css("border-width","0");$(this).parents(".item-column").css("border-width","1px");var id=$(this).parents(".anchorPoint").attr("id");var obj={column_id:id};parent.postMessage(obj,"*")});$(".icon_copy").hover(function(){$(this).css("background-position","-137px -434px")},function(){$(this).css("background-position","-117px -434px")});window.addEventListener("message",function(event){if(event.data.id){$(".item-column").css("border-width","0");$(""+event.data.id+" .item-column").css("border-width","1px")}if(event.data=="proof_right"){window.location.reload();System.operateState.saveProofInitPage(Report.report_id,"proof_switch_text")}if(event.data=="proofPt_right"){window.location.reload();System.operateState.saveProofInitPage(Report.report_id,"proof_switch_word")}},false);$(window).resize(function(){calcHeight()})})})(Report,jQuery);window.onload=function(){parent.parent.postMessage("Page_Loading_Right","*")};