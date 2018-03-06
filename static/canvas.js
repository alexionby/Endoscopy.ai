$(function(){

  function Scene(real_canvas, main_canvas) {

    this.main_canvas = main_canvas;
    this.real_canvas = real_canvas;

    this.global_parameters = undefined;

    this.segm = undefined;
    this.segm_opacity = 100;
    this.segm_is_visible = true;

    this.image = undefined;
    this.image_opacity = 100;
    this.image_is_visible = true;

    this.vessels = undefined;
    this.vessels_parameters = undefined;
    this.vessels_opacity = 100;
    this.vessels_is_visible = true;

    this.radius = undefined;
    this.selected_pixel = undefined;

    this.dots = undefined;
    this.dots_opacity = 100;
    this.dots_is_visible = true;

    this.current_vessel = -1;          //state and vessels
    this.selected_vessels = [];
    this.selected_dots = [];

    this.max_width = 0;
    this.max_height = 0;

    this.multiplier = 1;

    this.model = 0;

    this.current_vessel_window = undefined;
    this.vessel_windows = [];

    this.harmonics = undefined;
    this.plot_params = undefined;

    this.states = ['parameters','report'];
    this.current_state = 'parameters';
    this.report_vessels = [];

    this.before_merge = {};
  }

  Scene.prototype.add_to_report = function() {
    if (this.current_vessel > -1) {
      this.report_vessels.push( this.current_vessel );
    }
  }

  Scene.prototype.set_visible_size = function(container) {
    this.max_width = container.width() * 0.99;
    this.max_height = container.height() * 0.99;
  }

  Scene.prototype.draw_vessels = function() {
    var real_canvas = this.real_canvas;
    var ctx_real = real_canvas.getContext('2d');

    var main_canvas = this.main_canvas;
    var ctx_main = main_canvas.getContext('2d');

    var vessels = this.vessels;

    ctx_main.save();
    ctx_main.globalAlpha = this.vessels_opacity / 100

    for ( const key in vessels ) {
      for ( const i in vessels[key] ) {
        ctx_main.beginPath();
        ctx_main.arc(vessels[key][i][1] * this.multiplier, vessels[key][i][0] * this.multiplier, 1, 0, 2 * math.PI, false);
        ctx_main.fillStyle = "rgb(255,0,0)";
        ctx_main.fill();
      }
    }

    for ( const key of this.report_vessels ) {
      for ( const i in vessels[key] ) {
        ctx_main.beginPath();
        ctx_main.arc(vessels[key][i][1] * this.multiplier, vessels[key][i][0] * this.multiplier, 1, 0, 2 * math.PI, false);
        ctx_main.fillStyle = "rgb(255,0,255)";
        ctx_main.fill();
      }
    }

    if ( this.current_state == 'parameters' ) {
      if (this.current_vessel > -1) {
        for ( const i of vessels[this.current_vessel] ) {
          ctx_main.beginPath();
          ctx_main.arc(i[1] * this.multiplier, i[0] * this.multiplier, 1, 0, 2 * math.PI, false);
          ctx_main.fillStyle = "rgb(0,255,255)";
          ctx_main.fill();
         }
      }
    }

    if ( this.current_state == 'parameters' ) {
      for ( const key of this.selected_vessels ) {
        for ( const i of vessels[key] ) {
          ctx_main.beginPath();
          ctx_main.arc(i[1] * this.multiplier, i[0] * this.multiplier, 1, 0, 2 * math.PI, false);
          ctx_main.fillStyle = "rgb(255,255,255)";
          ctx_main.fill();
        }
      }
    }

    if ( this.current_state == 'report' ) {
      for ( const key of this.report_vessels) {
        if (vessels[key] === undefined) {
          let index = this.report_vessels.indexOf(key);
          this.report_vessels.splice(index, 1);
        }

        ctx_main.font = "18px Arial";
        ctx_main.fillStyle = "cyan";
        ctx_main.textAlign = "center";
        ctx_main.fillText(key, this.multiplier * (vessels[key][0][1] + vessels[key].slice(-1)[0][1]) / 2 , this.multiplier * (vessels[key][0][0] + vessels[key].slice(-1)[0][0]) / 2);
      }
    }
    ctx_main.restore()
  }

  //merge is here!!!!

  Scene.prototype.merge_step_back = function() {

    for (const vessel in this.before_merge['vessels']) {
      this.vessels[vessel] = this.before_merge['vessels'][vessel];
    }
    for (const radius in this.before_merge['rads']) {
      this.radius[radius] = this.before_merge['rads'][radius];
    }
    for (const parameter in this.before_merge['params']) {
      this.vessels_parameters[parameter] = this.before_merge['params'][parameter];
    }

    this.draw_scene();
    this.draw_plot();
  }

  Scene.prototype.merge_vessels = function() {

    let that = this;

    if (this.selected_vessels.length >= 2) {

      let indexes = this.selected_vessels;

      let vessels = {}
      let rads = {}
      let params = {}

      for (const index of indexes) {
        vessels[index] = this.vessels[index];
        rads[index]    = this.radius[index];
        params[index]  = this.vessels_parameters[index];

        delete this.vessels[index];
        delete this.radius[index];
        delete this.vessels_parameters[index];
      }

      this.before_merge = {
        'vessels' : vessels,
        'rads' : rads,
        'params' : params
      };

      $.ajax({
        method: "POST",
        url: "/merge",
        dataType: 'json',
        data: { vessels: JSON.stringify(vessels),
                rads: JSON.stringify(rads),
                params : JSON.stringify(params),
              }
      }).done(function(response){

        console.log(response);

        let index = math.min(indexes);

        that.vessels[index] = response['vessel'];
        that.vessels_parameters[index] = response['params'];

        that.vessels_parameters[index].push(that.vessels[index].length);

        that.radius[index] = response['radius'];
        that.harmonics[index] = response['harmonics'];
        that.plot_params[index] = response['plot_params'];
        that.selected_vessels = [];
        that.current_vessel = index;

        $('#param3').text(math.round(that.vessels_parameters[index][2],4));
        $('#param4').text(math.round(that.vessels_parameters[index][3],4));
        $('#param5').text(that.vessels_parameters[index][4]);
        $('#param6').text(that.vessels_parameters[index][5]);
        $('#param7').text( +(that.plot_params[index]['area_under_curve']).toFixed(4) );
        $('#param8').text( +(that.plot_params[index]['bend_count']).toFixed(4) );
        $('#param9').text( +(that.plot_params[index]['mean_abs_peaks']).toFixed(4) );
        $('#param10').text( +(that.plot_params[index]['std_amplitude']).toFixed(4) );
        $('#param11').text( +(that.plot_params[index]['max_amplitude']).toFixed(4) );
        $('#param12').text( +(that.plot_params[index]['min_amplitude']).toFixed(4) );

        that.draw_scene();
        that.draw_plot(index);
      });


    }

  }

  Scene.prototype.clear_selected_vessels = function() {
    this.selected_vessels = [];
    this.draw_scene();
  }

  Scene.prototype.select_object = function() {

      var x,y;

      function getMousePos(canvas, evt) {
        var rect = canvas.getBoundingClientRect();
        return {
          x: evt.clientX - rect.left,
          y: evt.clientY - rect.top
        };
      }

      var dots = this.dots;
      var canvas = this.main_canvas;
      var that = this;

      $("canvas#main-canvas").contextmenu(function(evt){

        evt.preventDefault();
        evt.stopPropagation();

        var mousePos = getMousePos(canvas, evt);
        var min = 1000;
        var n = 0;
        var m = 0;
        var dot = undefined;

        for (key in dots) {
          var distance = math.pow(dots[key][1] * that.multiplier - mousePos.x, 2) + math.pow(dots[key][0] * that.multiplier - mousePos.y , 2);
          if (distance < min) {
            min = distance;
            dot = key;
          }
        }

        if (dot) {
          if (that.selected_dots.includes(dot)) {
            var index = that.selected_dots.indexOf(dot);
            that.selected_dots.splice(index, 1);
            that.draw_scene();
          } else {
            that.selected_dots.push(dot);
            that.draw_scene();
          }
          $('.dots td:last').text(that.selected_dots.length);
        }
      });

      canvas.addEventListener('click', function(evt) {

        let vessels = that.vessels;
        var mousePos = getMousePos(canvas, evt);
        var min = 1000;
        var n = 0;
        var m = 0;
        var vessel = undefined;

        for (const key in vessels) {
          for (const i in vessels[key] ) {

            var distance = math.pow(vessels[key][i][1] * that.multiplier - mousePos.x, 2) + math.pow(vessels[key][i][0] * that.multiplier - mousePos.y , 2);
            if (distance < min) {
              min = distance;
              n = vessels[key][i][1];
              m = vessels[key][i][0];
              vessel = key;

              that.selected_pixel = [n,m,that.radius[key][i]];
            }
          }
        }

        if (evt.ctrlKey) {

          if (that.selected_vessels.includes(vessel)) {
            that.selected_vessels.splice(that.selected_vessels.indexOf(vessel), 1);
          } else {
            that.selected_vessels.push(vessel);
          }
        }

        $('#param2').text(that.selected_pixel[2]);

        if (that.current_vessel !== vessel) {

          that.current_vessel = vessel;

          $('#param3').text(math.round(that.vessels_parameters[vessel][2],4));
          $('#param4').text(math.round(that.vessels_parameters[vessel][3],4));
          $('#param5').text(that.vessels_parameters[vessel][4]);
          $('#param6').text(that.vessels_parameters[vessel][5]);
          $('#param7').text( +(that.plot_params[vessel]['area_under_curve']).toFixed(4) );
          $('#param8').text( +(that.plot_params[vessel]['bend_count']).toFixed(4) );
          $('#param9').text( +(that.plot_params[vessel]['mean_abs_peaks']).toFixed(4) );
          $('#param10').text( +(that.plot_params[vessel]['std_amplitude']).toFixed(4) );
          $('#param11').text( +(that.plot_params[vessel]['max_amplitude']).toFixed(4) );
          $('#param12').text( +(that.plot_params[vessel]['min_amplitude']).toFixed(4) );
          $('#param13').text( +(that.plot_params[vessel]['mean_peaks']).toFixed(4) );
          $('#param14').text( +(that.plot_params[vessel]['std_peaks']).toFixed(4) );

          that.draw_plot(vessel);
        }

        that.draw_scene();

      }, false);
  }

  Scene.prototype.draw_plot = function(index) {

    var trace1 = {
    x: this.harmonics[index][0],
    y: this.harmonics[index][1].map(Math.sqrt),
    mode: 'markers',
    marker: { size: 5 }
    };

    Plotly.newPlot('harmonic-plot', [trace1], layout, {scrollZoom: true, displayModeBar: false});

  }

  Scene.prototype.draw_dots = function() {

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    for ( const key in this.dots) {

      ctx_main.globalAlpha = this.dots_opacity / 100 * this.dots_is_visible;
      ctx_main.beginPath();
      ctx_main.arc(this.dots[key][1] * this.multiplier, this.dots[key][0] * this.multiplier, 3, 0, 2 * math.PI, false);
      ctx_main.fillStyle = "rgb(255,255,0)";
      ctx_main.fill();

    }

    for ( const key of this.selected_dots) {

      ctx_main.globalAlpha = this.dots_opacity / 100 * this.dots_is_visible;
      ctx_main.beginPath();
      ctx_main.arc(this.dots[key][1] * this.multiplier, this.dots[key][0] * this.multiplier, 3, 0, 2 * math.PI, false);
      ctx_main.fillStyle = "rgb(0,255,255)";
      ctx_main.fill();

    }

    ctx_main.restore();

  }

  Scene.prototype.draw_image = function() {

    var ctx_real = this.real_canvas.getContext('2d');
    ctx_real.drawImage(this.image, 0, 0, this.real_canvas.width, this.real_canvas.height);

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    ctx_main.globalAlpha = this.image_opacity / 100 * this.image_is_visible
    ctx_main.drawImage(this.image, 0, 0, this.main_canvas.width, this.main_canvas.height);
    ctx_main.restore();

  }

  Scene.prototype.draw_segm_image = function() {

    var ctx_real = this.real_canvas.getContext('2d');
    ctx_real.drawImage(this.segm, 0, 0, this.real_canvas.width, this.real_canvas.height);

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    ctx_main.globalAlpha = this.segm_opacity / 100 * this.segm_is_visible
    ctx_main.drawImage(this.segm, 0, 0, this.main_canvas.width, this.main_canvas.height);
    ctx_main.restore();

  }

  Scene.prototype.draw_scene = function() {

    var ctx_real = this.real_canvas.getContext('2d');

    this.real_canvas.width = this.image.width;
    this.real_canvas.height = this.image.height;

    var ctx_main = this.main_canvas.getContext('2d');

    this.multiplier = math.min( this.max_width / this.image.width , this.max_height / this.image.height );
    this.main_canvas.width =  this.image.width * this.multiplier;
    this.main_canvas.height = this.image.height * this.multiplier;

    if(typeof this.segm !== 'undefined'  && this.segm_is_visible !== false) {
      this.draw_segm_image();
    }
    if(typeof this.image !== 'undefined'  && this.image_is_visible !== false) {
      this.draw_image();
    }
    if(typeof this.vessels !== 'undefined' && this.vessels_is_visible !== false) {
      this.draw_vessels();
    }
    if(typeof this.dots !== 'undefined') {
      this.draw_dots();
    }
    if(typeof this.selected_pixel !== 'undefined') {
      this.draw_selected_pixel();
    }
  }

  Scene.prototype.draw_selected_pixel = function() {

    var ctx_main = this.main_canvas.getContext('2d');

    ctx_main.save();
    ctx_main.beginPath();
    ctx_main.arc(this.selected_pixel[0] * this.multiplier, this.selected_pixel[1] * this.multiplier, 2, 0, 2 * math.PI, false);
    ctx_main.fillStyle = "rgb(0,0,255)";
    ctx_main.fill();
    ctx_main.restore();
  }

  Scene.prototype.set_visibility = function(element) {

    this[element.id.split('-')[0] + '_is_visible'] = !this[element.id.split('-')[0] + '_is_visible'];
    this.draw_scene();
  }


  Scene.prototype.set_opacity = function(element) {

    this[element.id.split('-')[0] + '_opacity'] = element.value;
    this.draw_scene();
  }

  Scene.prototype.open_image = function(element) {

    $('#open-image-btn').html($('#open-image')[0].files[0].name);

    if ( $("#model").val() === "0") {
      $(".menu-buttons li:nth-child(1)").css("animation","");
      $(".menu-buttons li:nth-child(2)").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });
    }

    $('tr.bg-primary td:nth-child(2n)').text('0')

    var date = + new Date()
    document.cookie = "filename=" + date

    var that = this;
    var fr = new FileReader();
    fr.onload = function(){createImage(that)};
    fr.readAsDataURL($( element )[0].files[0]); //!!!!

    function createImage(scene) {

        scene.image = new Image();
        scene.image.onload = function(){ imageLoaded(scene) };
        scene.image.src = fr.result;
    }

    function imageLoaded(that) {

      that.multiplier = 1;

      that.image_opacity = 100;
      that.image_is_visible = true;

      that.vessels = undefined;
      that.vessels_parameters = undefined;
      that.vessels_opacity = 100;
      that.vessels_is_visible = true;

      that.dots = undefined;
      that.dots_opacity = 100;
      that.dots_is_visible = true;

      that.global_parameters = undefined;

      that.radius = undefined;
      that.selected_pixel = undefined;

      that.current_vessel = -1;
      that.selected_vessels = [];
      that.selected_dots = [];

      that.current_vessel_window = undefined;
      that.vessel_windows = [];

      that.harmonics = undefined;
      that.plot_params = undefined;

      that.report_vessels = [];

      $(":checkbox").prop('checked', true);
      $(".menu-layer input[type=range]").val(100);

      that.draw_scene();
      }

    }

  Scene.prototype.segment_image = function() {

    $('#segment-image').prop('disabled', true);

    $("#segment-image").text("Please, wait");
    $("#segment-image").css({
      "animation": "waiting",
      "animation-duration" : "2s",
      "animation-iteration-count" : "infinite",
    });

    var dataURL = this.real_canvas.toDataURL()
    var blobBin = atob(dataURL.split(',')[1]);
    var array = [];
    for(var i = 0; i < blobBin.length; i++) {
        array.push(blobBin.charCodeAt(i));
    }

    function _arrayBufferToBase64(buffer) {

        var binary = '';
        var bytes = new Uint8Array(buffer);
        var len = bytes.byteLength;
        for (var i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    };

    var file=new Blob([new Uint8Array(array)], {type: 'image/png'});

    var formdata = new FormData();
    formdata.append("img", file);
    formdata.append("model", this.model )
    formdata.append("filename", document.cookie)

    var that = this;

    $.ajax({
       url: "/segm",
       type: "POST",
       data: formdata,
       processData: false,
       contentType: false,
    }).done(function(respond){

      that.segm = new Image();
      that.image = new Image();
      var image_ready = function() {

        that.draw_scene();
        that.select_object();

      }

      that.vessels = respond['vessels'];
      that.vessels_parameters = respond['parameters'];

      for ( key in that.vessels ) {
          that.vessels_parameters[key].push(that.vessels[key].length);
      }

      console.log(respond['parameters']);
      console.log(respond['vessels']);

      that.radius = respond['radius'];

      that.global_parameters = respond['global_params']
      $('.global .param_value')[0].innerHTML = that.global_parameters['L']
      $('.global .param_value')[1].innerHTML = that.global_parameters['S']
      $('.global .param_value')[2].innerHTML = that.global_parameters['NonZero']
      $('.global .param_value')[3].innerHTML = math.round(that.global_parameters['lo'],4)
      $('.global .param_value')[4].innerHTML = math.round(that.global_parameters['B'],4)
      $('.global .param_value')[5].innerHTML = math.round(that.global_parameters['Si'],4)

      that.harmonics = respond['harmonics'];
      that.plot_params = respond['plot_params'];

      that.dots = respond['dots'];
      $('.dots .param_value')[0].innerHTML = Object.keys(that.dots).length

      that.segm.src = respond['path_segm'];

      that.image.onload = image_ready;
      that.image.src = respond['path'];



      $('#segment-image').prop('disabled', false);
      $("#segment-image").text("Processing");
      $("#segment-image").css("animation","");
    });

  }

  var scene = new Scene( $("#real-canvas")[0], $("#main-canvas")[0] );

  scene.set_visible_size( $('.image') );
  $( window ).resize(function() {

    scene.set_visible_size( $('.image') );
    scene.draw_scene();

  });

  $('#modeTab a#report-tab').click(function (e) {
    e.preventDefault();
    $(this).tab('show');
    scene.current_state = 'report';
    scene.draw_scene();

    $("ul#report-list").empty();

    for (const vessel of scene.report_vessels ) {
      $("ul#report-list").append('<li><span>' + vessel + '</span><button type="button" class="btn btn-danger">Del</button></li>');
    }

  });

  $('#modeTab a#parameters-tab').click(function (e) {
    scene.current_state = 'parameters';
  });


  // EXPORT

  $('#save_report_global_ref').click( function(that=this) {

    var filename, csv, element;
    var columnDelimiter = ';';
    var lineDelimiter = '\n';

    var keys = Object.keys(scene.global_parameters);
    var result = '';

    result += keys.join(columnDelimiter);
    result += lineDelimiter;

    for (const key of keys) {
      result += String(scene.global_parameters[key]).replace('.',',');
      result += columnDelimiter;
    }

    csv = result.slice(0,-1) + lineDelimiter;
    //csv = csv.replace(/./g, ',');

    element = $("#save_report_global_ref");

    filename = element.prev().val() + '.csv' ;

    if (!csv.match(/^data:text\/csv/i)) {
      csv = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURI(csv);
    }

    element.attr({
      "type": "hidden",
      "href": csv,
      "download": filename });
  });

  $('#save_report_csv_ref').click( function() {

    var data = []
    var temp_link, filename, csv;
    var index_and_params = []

    for ( const key of scene.report_vessels ) {

      index_and_params = [key].concat(scene.vessels_parameters[key]);
      index_and_params = index_and_params.concat(scene.harmonics[key][0]);
      index_and_params = index_and_params.concat(scene.harmonics[key][1]);
      index_and_params = index_and_params.concat(scene.plot_params[key]);

      data.push(index_and_params);
    }

    var columnDelimiter = ';';
    var lineDelimiter = '\n';

    var header = ['Id','Min. radius', 'Max. radius', 'Avr. radius','Std radius', 'Area', 'Length']
      .concat(["x0","x1","x2","x3","x4","x5","x6","x7","x8","x9"])
      .concat([0,1,2,3,4,5,6,7,8,9])
      .concat(['Area Under Curve','Bend Count','Max. amplitude',
               'Mean peaks amplitude', 'Avr amplitude', 'Min. amplitude', 'Std. amplitude', 'Std peaks']);

    /*
    var header = ['Id','Min. radius', 'Max. radius', 'Avr. radius','Std radius', 'Area']
       .concat(["x0","x1","x2","x3","x4","x5","x6","x7","x8","x9"])
       .concat([0,1,2,3,4,5,6,7,8,9])
       .concat(['Площадь под кривой','Количество перегибов','Макс. амплитуда',
                'Средняя амплитуда пиков', 'Средняя амплитуда', 'Мин. амплитуда', 'Дисперсия амплитуды', 'Дисперсия пиков']);
    */

    var keys = []
    keys = keys.concat(Object.keys(index_and_params)); //.concat( Object.keys(scene.plot_params) ) ;
    keys = keys.concat(Object.keys(scene.plot_params[0]));

    console.log(keys);
    console.log(index_and_params);

    var result = '';
    result += header.join(columnDelimiter);
    result += lineDelimiter;

    data.forEach(function(item) {

        var ctr = 0;
        keys.forEach(function( key ) {

            if (key === "27") {
              return 0
            }

            if (ctr > 0) { result += columnDelimiter;}

            if (key === "7") {
              result += 0
            } else {
              result += String(item[key] || item[ item.length - 1 ][key]).replace('.',',');
            }

            ctr++;
        });
        result += lineDelimiter;
    });

    filename = $("#save_report_csv_ref").prev().val() + '.csv' ;

    csv = result;
    //csv = result.replace(/./g, ',');

    if (!csv.match(/^data:text\/csv/i)) {
      csv = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURI(csv);
    }

    temp_link = $("#save_report_csv_ref")[0]; //document.createElement('a');
    temp_link.setAttribute("type", "hidden"); // make it hidden if needed
    temp_link.setAttribute('href', csv);
    temp_link.setAttribute('download', filename);
  });

  $('#save_report_img_ref').click( function(e) {

    $(this).attr({'href': $("#main-canvas")[0].toDataURL('image/png') , 'download': $(this).prev().val() + '.png'});
  });

  $('#modeTab a#parameters-tab').click(function (e) {
    e.preventDefault()
    $(this).tab('show')
    scene.draw_scene();
  });

  $('#report-list').on('click','button', function() {

    var index = scene.report_vessels.indexOf( $(this).prev().text() );

    scene.report_vessels.splice( index, 1 );

    $(this).parent().remove();
    scene.draw_scene();
  });

  // ERASE DOTS DELETE LIST
  $("#erase-dots-btn").click( function(){
    scene.selected_dots = [];
    scene.draw_scene();
  });

  // DELETE DOTS
  $("#del-dots-btn").click( function(){

    for ( const key of scene.selected_dots ) {
      delete scene.dots[key];
    }

    $('.dots td.param_value').text(Object.keys(scene.dots).length);
    $('.dots td:last').text(0);

    scene.global_parameters['N'] = Object.keys(scene.dots).length;

    scene.global_parameters['B'] = math.divide( Object.keys(scene.dots).length , scene.global_parameters['L'])
    $('.global .param_value')[4].innerHTML = math.round( scene.global_parameters['B'], 4)

    scene.global_parameters['Si'] = math.divide( scene.global_parameters['lo'] , scene.global_parameters['B'])
    $('.global .param_value')[5].innerHTML = math.round( scene.global_parameters['Si'], 4)

    scene.selected_dots = [];
    scene.draw_scene();

  });

  $("#model").change( function(){

    this.model = $("#model").val();

    if (this.model === "0"){
      $('#segment-image').prop('disabled', true);

      $(".menu-buttons li:nth-child(2)").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });

    } else {
      $('#segment-image').prop('disabled', false);
      $(".menu-buttons li:nth-child(2)").css("animation","");
      $(".menu-buttons li:nth-child(3) * ").css({
        "animation": "attention",
        "animation-duration" : "2s",
        "animation-iteration-count" : "infinite"
      });
    }
  });


  var left_mouse_down = false;

  $('*').mousedown( function() {
    left_mouse_down = true;
  })

  $('*').mouseup( function() {
    left_mouse_down = false;
  })

  $("progress").mousemove( function(event){

    if (left_mouse_down === true) {

      let elem = $(this);
      let bounds = elem[0].getBoundingClientRect();

      elem.val( math.round((event.pageX - bounds['x']) / bounds['width'] * 100));

      if ( elem.val() >= 98 | elem.val() <= 3) {

        scene[elem.attr('id').replace('-','_')] = elem.val();
        scene.draw_scene();
      }
    }
  });

  $("progress").mousedown( function(event){
    if (left_mouse_down === true) {
      let elem = $(this);
      let bounds = elem[0].getBoundingClientRect();
      elem.val( (event.pageX - bounds['x']) / bounds['width'] * 100);
    }
  });

  $(".menu-layer progress").mouseup( function(event){
    let elem = $(this);
    scene[elem.attr('id').replace('-','_')] = elem.val();
    scene.draw_scene();
  });

  $(".menu-layer span").css("pointer-events", "none");

  $("#open-image-btn").click(function(){
    console.log('open')
    $("#open-image").click();
    console.log($('input[type="file"]').val())
  });


  $("#open-image").change( function(){ scene.open_image(this); });
  $(":checkbox").change( function(){ scene.set_visibility(this); } );
  $("input[type=range]").change( function(){ scene.set_opacity(this); } );
  $("#segment-image").click( function(){ scene.segment_image(); });
  $("select#model").change( function(){ scene.model = this.value; });
  $("#merge_btn").click(function(){ scene.merge_vessels() });
  $("#clear_list_btn").click(function(){ scene.merge_step_back(); });
  $("#add_to_report_btn").click(function(){ scene.add_to_report(this); });
  $("#save-image-btn").click( function(){
    var dataURL = $("#main-canvas")[0].toDataURL('image/png');
    this.href = dataURL;
  });

  scene.model = "0";
  $('#model').val("0");
  $("#segment-image").prop('disabled',true);

  $(".menu-buttons li:nth-child(1)").css({
    "animation": "attention",
    "animation-duration" : "2s",
    "animation-iteration-count" : "infinite"
  });

});
