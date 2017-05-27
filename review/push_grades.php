<?php

# Uses code from https://github.com/Brightspace/sample-LTI-WHMIS-quiz
# which appears to be based on the MIT licensed code of Andy Smith, (c) 2007.

require_once 'OAuth.php';
$endpoint     = 'https://brightspace.tudelft.nl/d2l/le/lti/Outcome';

// From: http://php.net/manual/en/function.file-get-contents.php
function post_socket_xml($endpoint, $data, $moreheaders=false) {
    $url = parse_url($endpoint);

    if (!isset($url['port'])) {
      if ($url['scheme'] == 'http') { $url['port']=80; }
      elseif ($url['scheme'] == 'https') { $url['port']=443; }
    }

    $url['query']=isset($url['query'])?$url['query']:'';

    $hostport = ':'.$url['port'];
    if ($url['scheme'] == 'http' && $hostport == ':80' ) $hostport = '';
    if ($url['scheme'] == 'https' && $hostport == ':443' ) $hostport = '';

    $url['protocol']=$url['scheme'].'://';
    $eol="\r\n";

  $uri = "/";
  if ( isset($url['path'])) $uri = $url['path'];
  if ( strlen($url['query']) > 0 ) $uri .= '?'.$url['query'];
  if ( strlen($url['fragment']) > 0 ) $uri .= '#'.$url['fragment'];

    $headers =  "POST ".$uri." HTTP/1.0".$eol.
                "Host: ".$url['host'].$hostport.$eol.
                "Referer: ".$url['protocol'].$url['host'].$url['path'].$eol.
                "Content-Length: ".strlen($data).$eol;
  if ( is_string($moreheaders) ) $headers .= $moreheaders;
  $len = strlen($headers);
  if ( substr($headers,$len-2) != $eol ) {
        $headers .= $eol;
  }
    $headers .= $eol.$data;
  // echo("\n"); echo($headers); echo("\n");
    // echo("PORT=".$url['port']);
    try {
      $fp = fsockopen($url['host'], $url['port'], $errno, $errstr, 30);
      if($fp) {
        fputs($fp, $headers);
        $result = '';
        while(!feof($fp)) { $result .= fgets($fp, 128); }
        fclose($fp);
        //removes headers
        $pattern="/^.*\r\n\r\n/s";
        $result=preg_replace($pattern,'',$result);
        return $result;
      }
  } catch(Exception $e) {
    return false;
  }
  return false;
}

function sendOAuthBodyPOST($method, $endpoint, $oauth_consumer_key, $oauth_consumer_secret, $content_type, $body)
{
    $hash = base64_encode(sha1($body, TRUE));

    $parms = array('oauth_body_hash' => $hash);

    $test_token = '';
    $hmac_method = new OAuthSignatureMethod_HMAC_SHA1();
    $test_consumer = new OAuthConsumer($oauth_consumer_key, $oauth_consumer_secret, NULL);

    $acc_req = OAuthRequest::from_consumer_and_token($test_consumer, $test_token, $method, $endpoint, $parms);
    $acc_req->sign_request($hmac_method, $test_consumer, $test_token);

    // Pass this back up "out of band" for debugging
    global $LastOAuthBodyBaseString;
    $LastOAuthBodyBaseString = $acc_req->get_signature_base_string();
    // echo($LastOAuthBodyBaseString."\n");

    $header = $acc_req->to_header();
    $header = $header . "\r\nContent-Type: " . $content_type . "\r\n";

    $response = post_socket_xml($endpoint,$body,$header);
    if ( $response !== false && strlen($response) > 0) return $response;

    $params = array('http' => array(
        'method' => 'POST',
        'content' => $body,
        'header' => $header
        ));

    $ctx = stream_context_create($params);
  try {
    $fp = @fopen($endpoint, 'r', false, $ctx);
    } catch (Exception $e) {
        $fp = false;
    }
    if ($fp) {
        $response = @stream_get_contents($fp);
    } else {  // Try CURL
        $headers = explode("\r\n",$header);
        $response = sendXmlOverPost($endpoint, $body, $headers);
    }

    if ($response === false) {
        throw new Exception("Problem reading data from $endpoint, $php_errormsg");
    }
    return $response;
}

function parseResponse($response) {
    $retval = Array();
    try {
        $xml = new SimpleXMLElement($response);
        $imsx_header = $xml->imsx_POXHeader->children();
        $parms = $imsx_header->children();
        $status_info = $parms->imsx_statusInfo;
        $retval['imsx_codeMajor'] = (string) $status_info->imsx_codeMajor;
        $retval['imsx_severity'] = (string) $status_info->imsx_severity;
        $retval['imsx_description'] = (string) $status_info->imsx_description;
        $retval['imsx_messageIdentifier'] = (string) $parms->imsx_messageIdentifier;
        $imsx_body = $xml->imsx_POXBody->children();
        $operation = $imsx_body->getName();
        $retval['response'] = $operation;
        $parms = $imsx_body->children();
    } catch (Exception $e) {
        throw new Exception('Error: Unable to parse XML response' . $e->getMessage());
    }

    if ( $operation == 'readResultResponse' ) {
       try {
           $retval['language'] =(string) $parms->result->resultScore->language;
           $retval['textString'] = (string) $parms->result->resultScore->textString;
       } catch (Exception $e) {
            throw new Exception("Error: Body parse error: ".$e->getMessage());
       }
    }
    return $retval;
}

function getPOXRequest() {
    return '<?xml version = "1.0" encoding = "UTF-8"?>
<imsx_POXEnvelopeRequest xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>MESSAGE</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <OPERATION>
      <resultRecord>
        <sourcedGUID>
          <sourcedId>SOURCEDID</sourcedId>
        </sourcedGUID>
      </resultRecord>
    </OPERATION>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest>';
}


function getPOXGradeRequest() {
    return '<?xml version = "1.0" encoding = "UTF-8"?>
<imsx_POXEnvelopeRequest xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>MESSAGE</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <OPERATION>
      <resultRecord>
        <sourcedGUID>
          <sourcedId>SOURCEDID</sourcedId>
        </sourcedGUID>
        <result>
          <resultScore>
            <language>en-us</language>
            <textString>GRADE</textString>
          </resultScore>
        </result>
      </resultRecord>
    </OPERATION>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest>';
}


# Supply 4 options to this script
$longopts = array(
    "sourcedid:",
    "grade:",
    "oauth_consumer_key:",
    "oauth_consumer_secret:",
);
$options = getopt("", $longopts);
$sourcedid = $options['sourcedid'];
$grade = floatval($options['grade']);
$oauth_consumer_key = $options['oauth_consumer_key'];
$oauth_consumer_secret = $options['oauth_consumer_secret'];

#$postBody = str_replace(
#    array('SOURCEDID', 'OPERATION', 'MESSAGE'),
#    array($sourcedid, 'readResultRequest', uniqid()),
#    getPOXRequest());
#$response = parseResponse(sendOAuthBodyPOST('POST', $endpoint, $oauth_consumer_key, $oauth_consumer_secret, 'application/xml', $postBody));
#print_r ($response);
//if($response['imsx_codeMajor'] == 'success' && $response['textString'] != '') {
//    exit('Grade was already set in LMS - a cheater?!');
//}

// Submit the grade to the LMS with LTI
$postBody = str_replace(
	array('SOURCEDID', 'GRADE', 'OPERATION', 'MESSAGE'),
	array($sourcedid, $grade, 'replaceResultRequest', uniqid()),
	getPOXGradeRequest());

$response = sendOAuthBodyPOST('POST', $endpoint, $oauth_consumer_key, $oauth_consumer_secret, 'application/xml', $postBody);
$response = parseResponse($response);
if($response['imsx_codeMajor'] == 'success') {
    $result = 'Grade was set';
} else {
    $result = 'Grade set FAILED';
return $result;
}
?>